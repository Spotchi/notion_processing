#!/usr/bin/env python3
"""Test the booking service functionality."""

import os
os.environ['DATABASE_URL'] = 'sqlite:///./test_booking.db'

from notion_processing.booking_service import booking_service

def test_booking_service():
    print("Testing booking service...")
    
    # Test creating a customer
    customer = booking_service.create_customer('John Doe', 'john@example.com', '123-456-7890', 'Acme Corp')
    print(f'Created customer: {customer.name} ({customer.email})')

    # Test creating a booking request
    booking_request = booking_service.create_booking_request(
        customer_id=customer.id,
        service_type='Consulting',
        description='Need help with system integration',
        location='San Francisco'
    )
    print(f'Created booking request: {booking_request.id}')

    # Test creating a quote
    quote = booking_service.create_quote(
        booking_request_id=booking_request.id,
        price=5000.0,
        description='System integration consulting package',
        validity_days=30
    )
    print(f'Created quote: ${quote.price} (ID: {quote.id})')

    # Test confirming quote
    result = booking_service.confirm_quote(quote.id, True)
    print(f'Quote confirmation result: {result}')

    print('All booking service tests passed!')

if __name__ == "__main__":
    test_booking_service()