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
    Boolean,
    ForeignKey,
    create_engine,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import StaticPool

from .models import DocumentType, ProcessingStatus, SubCategory, BookingStatus, QuoteStatus

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


# Booking System Database Models

class CustomerDB(Base):
    """Database model for customers."""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    booking_requests = relationship("BookingRequestDB", back_populates="customer")


class BookingRequestDB(Base):
    """Database model for booking requests."""
    __tablename__ = "booking_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    preferred_date = Column(DateTime, nullable=True)
    location = Column(String, nullable=True)
    status = Column(Enum(BookingStatus), nullable=False, default=BookingStatus.PENDING)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("CustomerDB", back_populates="booking_requests")
    quotes = relationship("QuoteDB", back_populates="booking_request")


class QuoteDB(Base):
    """Database model for quotes."""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_request_id = Column(Integer, ForeignKey("booking_requests.id"), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    description = Column(Text, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    status = Column(Enum(QuoteStatus), nullable=False, default=QuoteStatus.PENDING)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by_customer = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking_request = relationship("BookingRequestDB", back_populates="quotes")


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self._engine = None
        self._SessionLocal = None
        self._database_url = database_url
    
    def _ensure_initialized(self):
        """Ensure the database manager is initialized."""
        if self._engine is not None:
            return
            
        database_url = self._database_url
        
        if database_url is None:
            # Try to get from environment variable first
            database_url = os.getenv("DATABASE_URL")
            
            # If not in environment, try to get from Streamlit secrets
            if database_url is None:
                try:
                    import streamlit as st
                    database_url = st.secrets.get("DATABASE_URL")
                except (ImportError, AttributeError, Exception):
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
        
        self._engine = create_engine(database_url, **engine_kwargs)
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )
    
    def create_tables(self):
        """Create all database tables."""
        self._ensure_initialized()
        Base.metadata.create_all(bind=self._engine)
    
    def get_session(self):
        """Get a database session."""
        self._ensure_initialized()
        return self._SessionLocal()
    
    def close(self):
        """Close database connections."""
        if self._engine:
            self._engine.dispose()


# Global database manager instance - will be initialized lazily
db_manager = DatabaseManager() 