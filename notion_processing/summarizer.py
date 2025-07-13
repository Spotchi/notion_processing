"""Weekly summary generator module."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import structlog
from openai import OpenAI

from .database import (
    DocumentClassificationDB,
    NotionDocumentDB,
    WeeklySummaryDB,
    db_manager,
)
from .models import DocumentType, SubCategory, WeeklySummary

logger = structlog.get_logger(__name__)


class WeeklySummarizer:
    """Generates weekly summaries of processed documents."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-mini-2025-04-14"):
        """Initialize the weekly summarizer."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
        # Summary prompt template
        self.summary_prompt = """
You are an expert analyst creating a weekly summary report that provides insights into the user's mindset and thinking patterns based on their document processing activity. Based on the provided data, create a comprehensive summary that includes:

1. **Executive Summary**: A high-level overview of the week's document processing activity and what it reveals about the user's current focus and interests
2. **Mindset Analysis**: Deep analysis of the user's thinking patterns, interests, and mental state based on the content and types of documents processed
3. **Document Distribution**: Analysis of document types and categories with insights into what this reveals about the user's priorities and areas of focus
4. **Key Insights**: Important patterns, trends, or notable findings about the user's mindset, interests, and cognitive patterns
5. **Recommendations**: Suggestions for leveraging insights about the user's mindset for personal development or productivity

Weekly Data:
- Total Documents: {total_documents}
- Document Types: {documents_by_type}
- Sub-categories: {documents_by_subcategory}
- Document Details: {document_details}

Document Contents:
{document_contents}

Please provide your response in the following JSON format:
{{
    "summary_text": "Comprehensive summary text focusing on mindset insights (2-3 paragraphs)",
    "key_insights": [
        "Mindset insight 1",
        "Mindset insight 2", 
        "Mindset insight 3"
    ]
}}

Focus on understanding the user's mindset, thinking patterns, interests, and mental state based on both the content and categorization of their documents.
"""

        logger.info("Weekly summarizer initialized", model=model)
    
    def get_weekly_documents(self, week_start: datetime, week_end: datetime) -> List[dict]:
        """Get documents processed in the specified week."""
        session = db_manager.get_session()
        
        try:
            # Get documents with their classifications for the week
            documents = session.query(
                NotionDocumentDB,
                DocumentClassificationDB
            ).join(
                DocumentClassificationDB,
                NotionDocumentDB.id == DocumentClassificationDB.document_id
            ).filter(
                NotionDocumentDB.created_time >= week_start,
                NotionDocumentDB.created_time <= week_end
            ).order_by(NotionDocumentDB.created_time.desc()).all()  # Most recent first
            
            document_details = []
            for doc, classification in documents:
                document_details.append({
                    "id": doc.id,
                    "title": doc.title,
                    "content": doc.content,
                    "type": classification.document_type.value,
                    "sub_category": classification.sub_category.value,
                    "confidence": classification.confidence_score,
                    "created_time": doc.created_time.isoformat()
                })
            
            logger.info("Retrieved weekly documents", count=len(document_details))
            return document_details
        
        except Exception as e:
            logger.error("Failed to get weekly documents", error=str(e))
            raise
        finally:
            session.close()
    
    def calculate_weekly_statistics(self, documents: List[dict]) -> dict:
        """Calculate statistics for the weekly documents."""
        total_documents = len(documents)
        
        # Count by document type
        documents_by_type = {}
        for doc in documents:
            doc_type = doc["type"]
            documents_by_type[doc_type] = documents_by_type.get(doc_type, 0) + 1
        
        # Count by sub-category
        documents_by_subcategory = {}
        for doc in documents:
            sub_category = doc["sub_category"]
            documents_by_subcategory[sub_category] = documents_by_subcategory.get(sub_category, 0) + 1
        
        return {
            "total_documents": total_documents,
            "documents_by_type": documents_by_type,
            "documents_by_subcategory": documents_by_subcategory
        }
    
    def generate_summary(self, week_start: datetime, week_end: datetime) -> WeeklySummary:
        """Generate a weekly summary report."""
        try:
            # Get documents for the week
            documents = self.get_weekly_documents(week_start, week_end)
            
            if not documents:
                logger.warning("No documents found for the specified week")
                return WeeklySummary(
                    week_start=week_start,
                    week_end=week_end,
                    total_documents=0,
                    documents_by_type={},
                    documents_by_subcategory={},
                    summary_text="No documents were processed during this week, making it difficult to analyze mindset patterns.",
                    key_insights=["No document activity to analyze for mindset insights this week."],
                )
            
            # Calculate statistics
            stats = self.calculate_weekly_statistics(documents)
            
            # Prepare document details for the prompt
            document_details = []
            for doc in documents[:20]:  # Limit to first 20 for prompt
                document_details.append(
                    f"- {doc['title']} ({doc['type']}/{doc['sub_category']}, confidence: {doc['confidence']:.2f})"
                )
            
            if len(documents) > 20:
                document_details.append(f"... and {len(documents) - 20} more documents")
            
            # Prepare document contents for the prompt (limit to first 10 documents to avoid token limits)
            document_contents = []
            for doc in documents[:10]:  # Limit to first 10 for content analysis
                content_preview = doc['content'][:500] if len(doc['content']) > 500 else doc['content']
                document_contents.append(
                    f"Document: {doc['title']} ({doc['type']}/{doc['sub_category']})\n"
                    f"Content Preview: {content_preview}\n"
                    f"{'...' if len(doc['content']) > 500 else ''}\n"
                )
            
            if len(documents) > 10:
                document_contents.append(f"... and {len(documents) - 10} more documents with content")
            
            # Prepare the prompt
            prompt = self.summary_prompt.format(
                total_documents=stats["total_documents"],
                documents_by_type=json.dumps(stats["documents_by_type"], indent=2),
                documents_by_subcategory=json.dumps(stats["documents_by_subcategory"], indent=2),
                document_details="\n".join(document_details),
                document_contents="\n".join(document_contents)
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analyst specializing in understanding human mindset and thinking patterns through document analysis. Your role is to provide insights into the user's mental state, interests, and cognitive patterns based on their document processing activity. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            try:
                # Remove any markdown formatting if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                summary_data = json.loads(response_text)
                
                # Create weekly summary
                weekly_summary = WeeklySummary(
                    week_start=week_start,
                    week_end=week_end,
                    total_documents=stats["total_documents"],
                    documents_by_type=stats["documents_by_type"],
                    documents_by_subcategory=stats["documents_by_subcategory"],
                    summary_text=summary_data.get("summary_text", ""),
                    key_insights=summary_data.get("key_insights", []),
                )
                
                logger.info(
                    "Weekly summary generated successfully",
                    week_start=week_start.date(),
                    week_end=week_end.date(),
                    total_documents=stats["total_documents"]
                )
                
                return weekly_summary
            
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error("Failed to parse summary response", error=str(e), response=response_text)
                raise ValueError(f"Invalid summary response: {response_text}")
        
        except Exception as e:
            logger.error("Failed to generate weekly summary", error=str(e))
            raise
    
    def save_summary_to_db(self, summary: WeeklySummary) -> None:
        """Save weekly summary to the database."""
        session = db_manager.get_session()
        
        try:
            # Check if summary already exists for this week
            existing_summary = session.query(WeeklySummaryDB).filter(
                WeeklySummaryDB.week_start == summary.week_start,
                WeeklySummaryDB.week_end == summary.week_end
            ).first()
            
            if existing_summary:
                # Update existing summary
                existing_summary.total_documents = summary.total_documents
                existing_summary.documents_by_type = json.dumps(summary.documents_by_type)
                existing_summary.documents_by_subcategory = json.dumps(summary.documents_by_subcategory)
                existing_summary.summary_text = summary.summary_text
                existing_summary.key_insights = json.dumps(summary.key_insights)
                existing_summary.generated_at = summary.generated_at
                logger.info("Updated existing weekly summary", week_start=summary.week_start.date())
            else:
                # Create new summary
                new_summary = WeeklySummaryDB(
                    week_start=summary.week_start,
                    week_end=summary.week_end,
                    total_documents=summary.total_documents,
                    documents_by_type=json.dumps(summary.documents_by_type),
                    documents_by_subcategory=json.dumps(summary.documents_by_subcategory),
                    summary_text=summary.summary_text,
                    key_insights=json.dumps(summary.key_insights),
                    generated_at=summary.generated_at
                )
                session.add(new_summary)
                logger.info("Created new weekly summary", week_start=summary.week_start.date())
            
            session.commit()
            logger.info("Saved weekly summary to database")
        
        except Exception as e:
            session.rollback()
            logger.error("Failed to save weekly summary to database", error=str(e))
            raise
        finally:
            session.close()
    
    def get_week_boundaries(self, date: Optional[datetime] = None) -> tuple[datetime, datetime]:
        """Get the start and end of the week for a given date."""
        if date is None:
            date = datetime.utcnow()
        
        # Start of week (Monday)
        week_start = date - timedelta(days=date.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # End of week (Sunday)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return week_start, week_end
    
    def run_weekly_summary(self, date: Optional[datetime] = None) -> WeeklySummary:
        """Run the complete weekly summary process."""
        logger.info("Starting weekly summary generation")
        
        # Get week boundaries
        week_start, week_end = self.get_week_boundaries(date)
        
        # Generate summary
        summary = self.generate_summary(week_start, week_end)
        
        # Save to database
        self.save_summary_to_db(summary)
        
        logger.info("Weekly summary completed successfully")
        return summary
    
    def get_mindset_insights(self, date: Optional[datetime] = None) -> dict:
        """Get detailed mindset insights for a specific week."""
        logger.info("Generating detailed mindset insights")
        
        # Get week boundaries
        week_start, week_end = self.get_week_boundaries(date)
        
        # Get documents for the week
        documents = self.get_weekly_documents(week_start, week_end)
        
        if not documents:
            return {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "insights": "No documents available for mindset analysis",
                "recommendations": ["Consider adding more documents to enable mindset analysis"]
            }
        
        # Calculate statistics
        stats = self.calculate_weekly_statistics(documents)
        
        # Analyze content patterns
        content_analysis = self._analyze_content_patterns(documents)
        
        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "total_documents": stats["total_documents"],
            "document_types": stats["documents_by_type"],
            "sub_categories": stats["documents_by_subcategory"],
            "content_patterns": content_analysis,
            "mindset_indicators": self._extract_mindset_indicators(documents)
        }
    
    def _analyze_content_patterns(self, documents: List[dict]) -> dict:
        """Analyze patterns in document content."""
        patterns = {
            "avg_content_length": 0,
            "content_themes": [],
            "writing_style_indicators": []
        }
        
        if not documents:
            return patterns
        
        # Calculate average content length
        total_length = sum(len(doc["content"]) for doc in documents)
        patterns["avg_content_length"] = total_length / len(documents)
        
        # Simple theme detection (can be enhanced with NLP)
        all_content = " ".join(doc["content"].lower() for doc in documents)
        common_words = ["learning", "project", "idea", "research", "work", "personal", "business"]
        patterns["content_themes"] = [word for word in common_words if word in all_content]
        
        return patterns
    
    def _extract_mindset_indicators(self, documents: List[dict]) -> List[str]:
        """Extract mindset indicators from documents."""
        indicators = []
        
        # Analyze document types for mindset patterns
        type_counts = {}
        for doc in documents:
            doc_type = doc["type"]
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Identify dominant patterns
        if type_counts.get("learning", 0) > len(documents) * 0.5:
            indicators.append("High focus on learning and personal development")
        
        if type_counts.get("project", 0) > len(documents) * 0.3:
            indicators.append("Active project management and execution mindset")
        
        if type_counts.get("research", 0) > len(documents) * 0.2:
            indicators.append("Research-oriented and analytical thinking")
        
        if type_counts.get("personal", 0) > len(documents) * 0.4:
            indicators.append("Strong personal reflection and self-awareness")
        
        return indicators 