"""Tests for booking and quote functionality."""

import pytest
from datetime import datetime, timedelta

from notion_processing.models import Quote, Booking, QuoteStatus


def test_quote_model_creation():
    """Test Quote model creation."""
    quote = Quote(
        customer_name="Test Customer",
        customer_email="test@example.com",
        service_description="Test service description",
        quoted_price=150.0,
        currency="USD",
        valid_until=datetime.utcnow() + timedelta(days=7),
        status=QuoteStatus.PENDING,
        notes="Test quote notes"
    )
    
    assert quote.customer_name == "Test Customer"
    assert quote.customer_email == "test@example.com"
    assert quote.quoted_price == 150.0
    assert quote.status == QuoteStatus.PENDING


def test_booking_model_creation():
    """Test Booking model creation."""
    booking = Booking(
        quote_id=1,
        customer_name="Test Customer",
        customer_email="test@example.com",
        service_description="Test service description",
        requested_date=datetime.utcnow() + timedelta(days=3),
        special_requirements="Test requirements"
    )
    
    assert booking.quote_id == 1
    assert booking.customer_name == "Test Customer"
    assert booking.customer_email == "test@example.com"


def test_quote_status_enum():
    """Test QuoteStatus enum values."""
    assert QuoteStatus.PENDING == "pending"
    assert QuoteStatus.CONFIRMED == "confirmed"
    assert QuoteStatus.REJECTED == "rejected"
    assert QuoteStatus.EXPIRED == "expired"


def test_quote_price_validation():
    """Test that quote price must be non-negative."""
    # This should work
    quote = Quote(
        customer_name="Test Customer",
        customer_email="test@example.com",
        service_description="Test service",
        quoted_price=0.0,  # Zero price should be allowed
        valid_until=datetime.utcnow() + timedelta(days=7)
    )
    assert quote.quoted_price == 0.0
    
    # Negative price should be caught by Pydantic validation
    try:
        Quote(
            customer_name="Test Customer",
            customer_email="test@example.com",
            service_description="Test service",
            quoted_price=-10.0,  # Negative price
            valid_until=datetime.utcnow() + timedelta(days=7)
        )
        assert False, "Should have raised validation error for negative price"
    except ValueError:
        assert True  # Expected validation error


if __name__ == "__main__":
    pytest.main([__file__])