"""Data models for the Notion processing pipeline."""

import json
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


class DocumentType(str, Enum):
    """Types of documents that can be classified."""
    PROJECT = "project"
    KNOWLEDGE = "knowledge"


class SubCategory(str, Enum):
    """Sub-categories for document classification."""
    # Project sub-categories
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    PLANNING = "planning"
    RESEARCH = "research"
    
    # Knowledge sub-categories
    TUTORIAL = "tutorial"
    REFERENCE = "reference"
    BEST_PRACTICE = "best_practice"
    CASE_STUDY = "case_study"
    DOCUMENTATION = "documentation"


class NotionDocument(BaseModel):
    """Model for raw Notion documents."""
    id: str = Field(..., description="Notion page ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    url: str = Field(..., description="Notion page URL")
    created_time: datetime = Field(..., description="Document creation time")
    last_edited_time: datetime = Field(..., description="Last edit time")
    parent_database_id: str = Field(..., description="Parent database ID")
    properties: Union[dict, str] = Field(default_factory=dict, description="Notion page properties")
    
    @field_validator('properties', mode='before')
    @classmethod
    def validate_properties(cls, v):
        """Ensure properties is always a dict."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}
    
    class Config:
        from_attributes = True


class DocumentClassification(BaseModel):
    """Model for document classification results."""
    document_id: str = Field(..., description="Notion document ID")
    document_type: DocumentType = Field(..., description="Primary classification")
    sub_category: SubCategory = Field(..., description="Sub-category classification")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    classification_reason: str = Field(..., description="Reason for classification")
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class WeeklySummary(BaseModel):
    """Model for weekly summary reports."""
    week_start: datetime = Field(..., description="Start of the week")
    week_end: datetime = Field(..., description="End of the week")
    total_documents: int = Field(..., description="Total documents processed")
    documents_by_type: dict[DocumentType, int] = Field(default_factory=dict)
    documents_by_subcategory: dict[SubCategory, int] = Field(default_factory=dict)
    summary_text: str = Field(..., description="Generated summary text")
    key_insights: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ProcessingStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    EXTRACTED = "extracted"
    CLASSIFIED = "classified"
    FAILED = "failed"


class ProcessingRecord(BaseModel):
    """Model for tracking processing status."""
    document_id: str = Field(..., description="Notion document ID")
    status: ProcessingStatus = Field(..., description="Current processing status")
    extracted_at: Optional[datetime] = Field(None, description="When extraction completed")
    classified_at: Optional[datetime] = Field(None, description="When classification completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


# Booking System Models

class BookingStatus(str, Enum):
    """Status of booking requests."""
    PENDING = "pending"
    QUOTED = "quoted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class QuoteStatus(str, Enum):
    """Status of quotes."""
    PENDING = "pending"
    SENT = "sent"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Customer(BaseModel):
    """Model for customer information."""
    id: Optional[int] = Field(None, description="Customer ID")
    name: str = Field(..., description="Customer name")
    email: str = Field(..., description="Customer email")
    phone: Optional[str] = Field(None, description="Customer phone number")
    company: Optional[str] = Field(None, description="Customer company")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    """Model for booking requests."""
    id: Optional[int] = Field(None, description="Booking request ID")
    customer_id: int = Field(..., description="Customer ID")
    service_type: str = Field(..., description="Type of service requested")
    description: str = Field(..., description="Detailed description of requirements")
    preferred_date: Optional[datetime] = Field(None, description="Preferred service date")
    location: Optional[str] = Field(None, description="Service location")
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="Booking status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class Quote(BaseModel):
    """Model for quotes."""
    id: Optional[int] = Field(None, description="Quote ID")
    booking_request_id: int = Field(..., description="Associated booking request ID")
    price: float = Field(..., ge=0, description="Quoted price")
    currency: str = Field(default="USD", description="Currency code")
    description: str = Field(..., description="Quote description")
    valid_until: datetime = Field(..., description="Quote expiration date")
    status: QuoteStatus = Field(default=QuoteStatus.PENDING, description="Quote status")
    confirmed_at: Optional[datetime] = Field(None, description="When quote was confirmed")
    confirmed_by_customer: bool = Field(default=False, description="Whether customer confirmed the quote")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True 