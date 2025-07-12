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
You are an expert analyst creating a weekly summary report of processed documents. Based on the provided data, create a comprehensive summary that includes:

1. **Executive Summary**: A high-level overview of the week's document processing activity
2. **Document Distribution**: Analysis of document types and categories
3. **Key Insights**: Important patterns, trends, or notable findings
4. **Recommendations**: Suggestions for action items or areas of focus

Weekly Data:
- Total Documents: {total_documents}
- Document Types: {documents_by_type}
- Sub-categories: {documents_by_subcategory}
- Document Details: {document_details}

Please provide your response in the following JSON format:
{{
    "summary_text": "Comprehensive summary text (2-3 paragraphs)",
    "key_insights": [
        "Insight 1",
        "Insight 2",
        "Insight 3"
    ]
}}

Focus on actionable insights and meaningful patterns in the data.
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
            ).all()
            
            document_details = []
            for doc, classification in documents:
                document_details.append({
                    "id": doc.id,
                    "title": doc.title,
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
                    summary_text="No documents were processed during this week.",
                    key_insights=["No activity to report for this week."]
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
            
            # Prepare the prompt
            prompt = self.summary_prompt.format(
                total_documents=stats["total_documents"],
                documents_by_type=json.dumps(stats["documents_by_type"], indent=2),
                documents_by_subcategory=json.dumps(stats["documents_by_subcategory"], indent=2),
                document_details="\n".join(document_details)
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert analyst creating weekly summary reports. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
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
                    key_insights=summary_data.get("key_insights", [])
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
                db_summary = WeeklySummaryDB(
                    week_start=summary.week_start,
                    week_end=summary.week_end,
                    total_documents=summary.total_documents,
                    documents_by_type=json.dumps(summary.documents_by_type),
                    documents_by_subcategory=json.dumps(summary.documents_by_subcategory),
                    summary_text=summary.summary_text,
                    key_insights=json.dumps(summary.key_insights),
                    generated_at=summary.generated_at
                )
                session.add(db_summary)
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