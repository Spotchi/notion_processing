"""Database configuration and models for PostgreSQL."""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .models import DocumentType, ProcessingStatus, SubCategory

Base = declarative_base()


class NotionDocumentDB(Base):
    """Database model for Notion documents."""
    __tablename__ = "notion_documents"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    created_time = Column(DateTime, nullable=False)
    last_edited_time = Column(DateTime, nullable=False)
    parent_database_id = Column(String, nullable=False)
    properties = Column(Text)  # JSON as text
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DocumentClassificationDB(Base):
    """Database model for document classifications."""
    __tablename__ = "document_classifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False, index=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    sub_category = Column(Enum(SubCategory), nullable=False)
    confidence_score = Column(Float, nullable=False)
    classification_reason = Column(Text, nullable=False)
    classified_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class WeeklySummaryDB(Base):
    """Database model for weekly summaries."""
    __tablename__ = "weekly_summaries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    total_documents = Column(Integer, nullable=False)
    documents_by_type = Column(Text)  # JSON as text
    documents_by_subcategory = Column(Text)  # JSON as text
    summary_text = Column(Text, nullable=False)
    key_insights = Column(Text)  # JSON as text
    generated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class ProcessingRecordDB(Base):
    """Database model for processing records."""
    __tablename__ = "processing_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, nullable=False, unique=True, index=True)
    status = Column(Enum(ProcessingStatus), nullable=False)
    extracted_at = Column(DateTime, nullable=True)
    classified_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        if database_url is None:
            # Try to get from environment variable first
            database_url = os.getenv("DATABASE_URL")
            
            # If not in environment, try to get from Streamlit secrets
            if database_url is None:
                try:
                    import streamlit as st
                    database_url = st.secrets.get("DATABASE_URL")
                except (ImportError, AttributeError):
                    # Streamlit not available or secrets not configured
                    pass
            
            # Fallback to default if still None
            if database_url is None:
                raise ValueError("DATABASE_URL is not set")
        
        # Configure engine with SSL for Supabase
        engine_kwargs = {
            "poolclass": StaticPool,
            "pool_pre_ping": True,
        }
        
        # Add SSL configuration for Supabase
        if "supabase.co" in database_url:
            engine_kwargs["connect_args"] = {
                "sslmode": "require"
            }
        
        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections."""
        self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager() 