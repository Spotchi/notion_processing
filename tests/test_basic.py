"""Basic tests for the Notion processing pipeline."""

import pytest
from datetime import datetime

from notion_processing.models import DocumentType, SubCategory, NotionDocument, DocumentClassification
from notion_processing.database import DatabaseManager


def test_document_type_enum():
    """Test DocumentType enum values."""
    assert DocumentType.PROJECT == "project"
    assert DocumentType.KNOWLEDGE == "knowledge"


def test_sub_category_enum():
    """Test SubCategory enum values."""
    assert SubCategory.FEATURE_REQUEST == "feature_request"
    assert SubCategory.BUG_REPORT == "bug_report"
    assert SubCategory.TUTORIAL == "tutorial"
    assert SubCategory.REFERENCE == "reference"


def test_notion_document_model():
    """Test NotionDocument model creation."""
    doc = NotionDocument(
        id="test-id",
        title="Test Document",
        content="Test content",
        url="https://notion.so/test",
        created_time=datetime.utcnow(),
        last_edited_time=datetime.utcnow(),
        parent_database_id="test-db"
    )
    
    assert doc.id == "test-id"
    assert doc.title == "Test Document"
    assert doc.content == "Test content"


def test_document_classification_model():
    """Test DocumentClassification model creation."""
    classification = DocumentClassification(
        document_id="test-id",
        document_type=DocumentType.PROJECT,
        sub_category=SubCategory.FEATURE_REQUEST,
        confidence_score=0.95,
        classification_reason="This is clearly a feature request"
    )
    
    assert classification.document_id == "test-id"
    assert classification.document_type == DocumentType.PROJECT
    assert classification.confidence_score == 0.95


def test_database_manager_initialization():
    """Test DatabaseManager initialization."""
    db_manager = DatabaseManager()
    assert db_manager is not None
    assert hasattr(db_manager, 'engine')
    assert hasattr(db_manager, 'SessionLocal')


def test_imports():
    """Test that all modules can be imported."""
    try:
        from notion_processing.extractor import NotionExtractor
        from notion_processing.classifier import DocumentClassifier
        from notion_processing.summarizer import WeeklySummarizer
        from notion_processing.pipeline import NotionProcessingPipeline
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__]) 