"""LLM-based document classifier module."""

import json
import os
from datetime import datetime
from typing import List, Optional

import structlog
from openai import OpenAI

from .database import (
    DocumentClassificationDB,
    NotionDocumentDB,
    ProcessingRecordDB,
    db_manager,
)
from .models import DocumentClassification, DocumentType, ProcessingStatus, SubCategory

logger = structlog.get_logger(__name__)


class DocumentClassifier:
    """LLM-based document classifier."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1-mini-2025-04-14"):
        """Initialize the document classifier."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        
        # Classification prompt template
        self.classification_prompt = """
You are a document classification expert. Your task is to classify the given document into one of the predefined categories.

Document Categories:
1. PROJECT - Documents related to project work, tasks, features, bugs, planning, etc.
   - feature_request: Requests for new features or functionality
   - bug_report: Reports of bugs or issues
   - planning: Project planning, roadmaps, timelines
   - research: Research findings, analysis, investigations

2. KNOWLEDGE - Documents containing knowledge, documentation, tutorials, etc.
   - tutorial: Step-by-step guides, how-to documents
   - reference: Reference materials, documentation, specifications
   - best_practice: Best practices, guidelines, standards
   - case_study: Case studies, examples, success stories
   - documentation: Technical documentation, API docs, etc.

Document Title: {title}

Document Content:
{content}

Please classify this document and provide your response in the following JSON format:
{{
    "document_type": "project" or "knowledge",
    "sub_category": "one of the sub-categories listed above",
    "confidence_score": 0.0 to 1.0,
    "classification_reason": "Brief explanation of why you chose this classification"
}}

Focus on the main purpose and content of the document. If the document could fit multiple categories, choose the most dominant one.
"""

        logger.info("Document classifier initialized", model=model)
    
    def classify_document(self, document: NotionDocumentDB) -> DocumentClassification:
        """Classify a single document."""
        try:
            # Prepare the prompt
            prompt = self.classification_prompt.format(
                title=document.title,
                content=document.content[:4000]  # Limit content length
            )
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a document classification expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                
                classification_data = json.loads(response_text)
                
                # Validate and create classification
                document_type = DocumentType(classification_data["document_type"])
                sub_category = SubCategory(classification_data["sub_category"])
                confidence_score = float(classification_data["confidence_score"])
                classification_reason = classification_data["classification_reason"]
                
                classification = DocumentClassification(
                    document_id=document.id,
                    document_type=document_type,
                    sub_category=sub_category,
                    confidence_score=confidence_score,
                    classification_reason=classification_reason
                )
                
                logger.info(
                    "Document classified successfully",
                    document_id=document.id,
                    document_type=document_type.value,
                    sub_category=sub_category.value,
                    confidence=confidence_score
                )
                
                return classification
            
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error("Failed to parse classification response", error=str(e), response=response_text)
                raise ValueError(f"Invalid classification response: {response_text}")
        
        except Exception as e:
            logger.error("Failed to classify document", document_id=document.id, error=str(e))
            raise
    
    def classify_documents_batch(self, documents: List[NotionDocumentDB]) -> List[DocumentClassification]:
        """Classify multiple documents in batch."""
        classifications = []
        
        for document in documents:
            try:
                classification = self.classify_document(document)
                classifications.append(classification)
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)
            
            except Exception as e:
                logger.error("Failed to classify document in batch", document_id=document.id, error=str(e))
                # Continue with other documents
                continue
        
        return classifications
    
    def save_classifications_to_db(self, classifications: List[DocumentClassification]) -> None:
        """Save classifications to the database."""
        session = db_manager.get_session()
        
        try:
            for classification in classifications:
                # Check if classification already exists
                existing_classification = session.query(DocumentClassificationDB).filter(
                    DocumentClassificationDB.document_id == classification.document_id
                ).first()
                
                if existing_classification:
                    # Update existing classification
                    existing_classification.document_type = classification.document_type
                    existing_classification.sub_category = classification.sub_category
                    existing_classification.confidence_score = classification.confidence_score
                    existing_classification.classification_reason = classification.classification_reason
                    existing_classification.classified_at = classification.classified_at
                    logger.info("Updated existing classification", document_id=classification.document_id)
                else:
                    # Create new classification
                    db_classification = DocumentClassificationDB(
                        document_id=classification.document_id,
                        document_type=classification.document_type,
                        sub_category=classification.sub_category,
                        confidence_score=classification.confidence_score,
                        classification_reason=classification.classification_reason,
                        classified_at=classification.classified_at
                    )
                    session.add(db_classification)
                    logger.info("Created new classification", document_id=classification.document_id)
                
                # Update processing record
                processing_record = session.query(ProcessingRecordDB).filter(
                    ProcessingRecordDB.document_id == classification.document_id
                ).first()
                
                if processing_record:
                    processing_record.status = ProcessingStatus.CLASSIFIED
                    processing_record.classified_at = datetime.utcnow()
                    processing_record.updated_at = datetime.utcnow()
                else:
                    processing_record = ProcessingRecordDB(
                        document_id=classification.document_id,
                        status=ProcessingStatus.CLASSIFIED,
                        classified_at=datetime.utcnow()
                    )
                    session.add(processing_record)
            
            session.commit()
            logger.info("Saved classifications to database", count=len(classifications))
        
        except Exception as e:
            session.rollback()
            logger.error("Failed to save classifications to database", error=str(e))
            raise
        finally:
            session.close()
    
    def get_unclassified_documents(self) -> List[NotionDocumentDB]:
        """Get documents that haven't been classified yet."""
        session = db_manager.get_session()
        
        try:
            # Get documents that are extracted but not classified
            unclassified_docs = session.query(NotionDocumentDB).join(
                ProcessingRecordDB,
                NotionDocumentDB.id == ProcessingRecordDB.document_id
            ).filter(
                ProcessingRecordDB.status == ProcessingStatus.EXTRACTED
            ).all()
            
            logger.info("Found unclassified documents", count=len(unclassified_docs))
            return unclassified_docs
        
        except Exception as e:
            logger.error("Failed to get unclassified documents", error=str(e))
            raise
        finally:
            session.close()
    
    def run_classification(self) -> List[DocumentClassification]:
        """Run the complete classification process."""
        logger.info("Starting document classification")
        
        # Get unclassified documents
        unclassified_docs = self.get_unclassified_documents()
        
        if not unclassified_docs:
            logger.info("No unclassified documents found")
            return []
        
        # Classify documents
        classifications = self.classify_documents_batch(unclassified_docs)
        
        # Save to database
        self.save_classifications_to_db(classifications)
        
        logger.info("Classification completed successfully", classification_count=len(classifications))
        return classifications 