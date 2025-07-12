"""Notion document extractor module."""

import json
import os
from datetime import datetime
from typing import List, Optional

import structlog
from notion_client import Client
from notion_client.errors import APIResponseError

from .database import NotionDocumentDB, ProcessingRecordDB, db_manager
from .models import NotionDocument, ProcessingStatus

logger = structlog.get_logger(__name__)


class NotionExtractor:
    """Extracts documents from Notion databases."""
    
    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        """Initialize the Notion extractor."""
        self.token = token or os.getenv("NOTION_TOKEN")
        if not self.token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN environment variable.")
        
        self.database_id = database_id or os.getenv("NOTION_DATABASE_ID")
        if not self.database_id:
            raise ValueError("Notion database ID is required. Set NOTION_DATABASE_ID environment variable.")
        
        self.client = Client(auth=self.token)
        logger.info("Notion extractor initialized", database_id=self.database_id)
    
    def extract_page_content(self, page_id: str) -> str:
        """Extract content from a Notion page."""
        try:
            # Get page content
            blocks = self.client.blocks.children.list(page_id)
            content_parts = []
            
            for block in blocks["results"]:
                if block["type"] == "paragraph":
                    rich_text = block["paragraph"]["rich_text"]
                    if rich_text:
                        content_parts.append(" ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "heading_1":
                    rich_text = block["heading_1"]["rich_text"]
                    if rich_text:
                        content_parts.append("# " + " ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "heading_2":
                    rich_text = block["heading_2"]["rich_text"]
                    if rich_text:
                        content_parts.append("## " + " ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "heading_3":
                    rich_text = block["heading_3"]["rich_text"]
                    if rich_text:
                        content_parts.append("### " + " ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "bulleted_list_item":
                    rich_text = block["bulleted_list_item"]["rich_text"]
                    if rich_text:
                        content_parts.append("- " + " ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "numbered_list_item":
                    rich_text = block["numbered_list_item"]["rich_text"]
                    if rich_text:
                        content_parts.append("1. " + " ".join([text["plain_text"] for text in rich_text]))
                elif block["type"] == "code":
                    rich_text = block["code"]["rich_text"]
                    if rich_text:
                        content_parts.append("```\n" + " ".join([text["plain_text"] for text in rich_text]) + "\n```")
            
            return "\n\n".join(content_parts)
        
        except APIResponseError as e:
            logger.error("Failed to extract page content", page_id=page_id, error=str(e))
            raise
    
    def extract_page_title(self, page: dict) -> str:
        """Extract title from a Notion page."""
        properties = page.get("properties", {})
        
        # Try different title properties
        title_properties = ["title", "Name", "name", "Title"]
        for prop_name in title_properties:
            if prop_name in properties:
                prop = properties[prop_name]
                if prop["type"] == "title" and prop["title"]:
                    return " ".join([text["plain_text"] for text in prop["title"]])
        
        # Fallback to page ID if no title found
        return f"Untitled Page ({page['id'][:8]})"
    
    def extract_documents_from_database(self, limit: Optional[int] = None) -> List[NotionDocument]:
        """Extract all documents from the specified database."""
        documents = []
        
        try:
            # Query the database
            query_params = {
                "database_id": self.database_id,
                "page_size": 100,  # Maximum page size
            }
            
            if limit:
                query_params["page_size"] = min(limit, 100)
            
            response = self.client.databases.query(**query_params)
            pages = response["results"]
            
            logger.info("Found pages in database", count=len(pages))
            
            for page in pages:
                try:
                    # Extract page content
                    content = self.extract_page_content(page["id"])
                    
                    # Extract title
                    title = self.extract_page_title(page)
                    
                    # Create document
                    document = NotionDocument(
                        id=page["id"],
                        title=title,
                        content=content,
                        url=page["url"],
                        created_time=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
                        last_edited_time=datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00")),
                        parent_database_id=self.database_id,
                        properties=page.get("properties", {})  # Keep as dict, not JSON string
                    )
                    
                    documents.append(document)
                    logger.info("Extracted document", document_id=page["id"], title=title)
                
                except Exception as e:
                    logger.error("Failed to extract page", page_id=page["id"], error=str(e))
                    # Continue with other pages
                    continue
            
            # Handle pagination if needed
            while response.get("has_more") and (limit is None or len(documents) < limit):
                query_params["start_cursor"] = response["next_cursor"]
                response = self.client.databases.query(**query_params)
                pages = response["results"]
                
                for page in pages:
                    if limit and len(documents) >= limit:
                        break
                    
                    try:
                        content = self.extract_page_content(page["id"])
                        title = self.extract_page_title(page)
                        
                        document = NotionDocument(
                            id=page["id"],
                            title=title,
                            content=content,
                            url=page["url"],
                            created_time=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
                            last_edited_time=datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00")),
                            parent_database_id=self.database_id,
                            properties=page.get("properties", {})  # Keep as dict, not JSON string
                        )
                        
                        documents.append(document)
                        logger.info("Extracted document", document_id=page["id"], title=title)
                    
                    except Exception as e:
                        logger.error("Failed to extract page", page_id=page["id"], error=str(e))
                        continue
                
                if limit and len(documents) >= limit:
                    break
            
            logger.info("Extraction completed", total_documents=len(documents))
            return documents
        
        except APIResponseError as e:
            logger.error("Failed to query database", database_id=self.database_id, error=str(e))
            raise
    
    def save_documents_to_db(self, documents: List[NotionDocument]) -> None:
        """Save extracted documents to the database."""
        session = db_manager.get_session()
        
        try:
            for document in documents:
                # Check if document already exists
                existing_doc = session.query(NotionDocumentDB).filter(
                    NotionDocumentDB.id == document.id
                ).first()
                
                if existing_doc:
                    # Update existing document
                    existing_doc.title = document.title
                    existing_doc.content = document.content
                    existing_doc.last_edited_time = document.last_edited_time
                    existing_doc.properties = json.dumps(document.properties)  # Convert to JSON for DB storage
                    existing_doc.updated_at = datetime.utcnow()
                    logger.info("Updated existing document", document_id=document.id)
                else:
                    # Create new document
                    db_document = NotionDocumentDB(
                        id=document.id,
                        title=document.title,
                        content=document.content,
                        url=document.url,
                        created_time=document.created_time,
                        last_edited_time=document.last_edited_time,
                        parent_database_id=document.parent_database_id,
                        properties=json.dumps(document.properties)  # Convert to JSON for DB storage
                    )
                    session.add(db_document)
                    logger.info("Created new document", document_id=document.id)
                
                # Update processing record
                processing_record = session.query(ProcessingRecordDB).filter(
                    ProcessingRecordDB.document_id == document.id
                ).first()
                
                if processing_record:
                    processing_record.status = ProcessingStatus.EXTRACTED
                    processing_record.extracted_at = datetime.utcnow()
                    processing_record.updated_at = datetime.utcnow()
                else:
                    processing_record = ProcessingRecordDB(
                        document_id=document.id,
                        status=ProcessingStatus.EXTRACTED,
                        extracted_at=datetime.utcnow()
                    )
                    session.add(processing_record)
            
            session.commit()
            logger.info("Saved documents to database", count=len(documents))
        
        except Exception as e:
            session.rollback()
            logger.error("Failed to save documents to database", error=str(e))
            raise
        finally:
            session.close()
    
    def run_extraction(self, limit: Optional[int] = None) -> List[NotionDocument]:
        """Run the complete extraction process."""
        logger.info("Starting Notion document extraction")
        
        # Extract documents
        documents = self.extract_documents_from_database(limit=limit)
        
        # Save to database
        self.save_documents_to_db(documents)
        
        logger.info("Extraction completed successfully", document_count=len(documents))
        return documents 