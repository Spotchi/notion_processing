"""Booking system service for managing quotes and bookings."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from .database import BookingRequestDB, CustomerDB, QuoteDB, db_manager
from .models import BookingRequest, BookingStatus, Customer, Quote, QuoteStatus


class BookingService:
    """Service for managing booking requests and quotes."""
    
    def __init__(self):
        """Initialize the booking service."""
        pass
    
    def create_customer(self, name: str, email: str, phone: Optional[str] = None, 
                       company: Optional[str] = None) -> Customer:
        """Create a new customer or return existing one."""
        session = db_manager.get_session()
        
        try:
            # Check if customer already exists
            existing_customer = session.query(CustomerDB).filter(
                CustomerDB.email == email
            ).first()
            
            if existing_customer:
                return Customer(
                    id=existing_customer.id,
                    name=existing_customer.name,
                    email=existing_customer.email,
                    phone=existing_customer.phone,
                    company=existing_customer.company,
                    created_at=existing_customer.created_at
                )
            
            # Create new customer
            db_customer = CustomerDB(
                name=name,
                email=email,
                phone=phone,
                company=company
            )
            session.add(db_customer)
            session.commit()
            session.refresh(db_customer)
            
            return Customer(
                id=db_customer.id,
                name=db_customer.name,
                email=db_customer.email,
                phone=db_customer.phone,
                company=db_customer.company,
                created_at=db_customer.created_at
            )
        
        finally:
            session.close()
    
    def create_booking_request(self, customer_id: int, service_type: str, 
                             description: str, preferred_date: Optional[datetime] = None,
                             location: Optional[str] = None) -> BookingRequest:
        """Create a new booking request."""
        session = db_manager.get_session()
        
        try:
            db_request = BookingRequestDB(
                customer_id=customer_id,
                service_type=service_type,
                description=description,
                preferred_date=preferred_date,
                location=location,
                status=BookingStatus.PENDING
            )
            session.add(db_request)
            session.commit()
            session.refresh(db_request)
            
            return BookingRequest(
                id=db_request.id,
                customer_id=db_request.customer_id,
                service_type=db_request.service_type,
                description=db_request.description,
                preferred_date=db_request.preferred_date,
                location=db_request.location,
                status=db_request.status,
                created_at=db_request.created_at,
                updated_at=db_request.updated_at
            )
        
        finally:
            session.close()
    
    def create_quote(self, booking_request_id: int, price: float, description: str,
                    currency: str = "USD", validity_days: int = 30) -> Quote:
        """Create a quote for a booking request."""
        session = db_manager.get_session()
        
        try:
            valid_until = datetime.utcnow() + timedelta(days=validity_days)
            
            db_quote = QuoteDB(
                booking_request_id=booking_request_id,
                price=price,
                currency=currency,
                description=description,
                valid_until=valid_until,
                status=QuoteStatus.SENT
            )
            session.add(db_quote)
            
            # Update booking request status
            booking_request = session.query(BookingRequestDB).filter(
                BookingRequestDB.id == booking_request_id
            ).first()
            if booking_request:
                booking_request.status = BookingStatus.QUOTED
            
            session.commit()
            session.refresh(db_quote)
            
            return Quote(
                id=db_quote.id,
                booking_request_id=db_quote.booking_request_id,
                price=db_quote.price,
                currency=db_quote.currency,
                description=db_quote.description,
                valid_until=db_quote.valid_until,
                status=db_quote.status,
                confirmed_at=db_quote.confirmed_at,
                confirmed_by_customer=db_quote.confirmed_by_customer,
                created_at=db_quote.created_at,
                updated_at=db_quote.updated_at
            )
        
        finally:
            session.close()
    
    def confirm_quote(self, quote_id: int, customer_confirmed: bool = True) -> bool:
        """Confirm or reject a quote."""
        session = db_manager.get_session()
        
        try:
            quote = session.query(QuoteDB).filter(QuoteDB.id == quote_id).first()
            if not quote:
                return False
            
            if customer_confirmed:
                quote.status = QuoteStatus.CONFIRMED
                quote.confirmed_by_customer = True
                quote.confirmed_at = datetime.utcnow()
                
                # Update booking request status
                booking_request = session.query(BookingRequestDB).filter(
                    BookingRequestDB.id == quote.booking_request_id
                ).first()
                if booking_request:
                    booking_request.status = BookingStatus.CONFIRMED
            else:
                quote.status = QuoteStatus.REJECTED
                quote.confirmed_by_customer = False
                
                # Update booking request status
                booking_request = session.query(BookingRequestDB).filter(
                    BookingRequestDB.id == quote.booking_request_id
                ).first()
                if booking_request:
                    booking_request.status = BookingStatus.REJECTED
            
            session.commit()
            return True
        
        finally:
            session.close()
    
    def get_booking_request(self, request_id: int) -> Optional[BookingRequest]:
        """Get a booking request by ID."""
        session = db_manager.get_session()
        
        try:
            db_request = session.query(BookingRequestDB).filter(
                BookingRequestDB.id == request_id
            ).first()
            
            if not db_request:
                return None
            
            return BookingRequest(
                id=db_request.id,
                customer_id=db_request.customer_id,
                service_type=db_request.service_type,
                description=db_request.description,
                preferred_date=db_request.preferred_date,
                location=db_request.location,
                status=db_request.status,
                created_at=db_request.created_at,
                updated_at=db_request.updated_at
            )
        
        finally:
            session.close()
    
    def get_quote_by_booking_request(self, request_id: int) -> Optional[Quote]:
        """Get the latest quote for a booking request."""
        session = db_manager.get_session()
        
        try:
            db_quote = session.query(QuoteDB).filter(
                QuoteDB.booking_request_id == request_id
            ).order_by(QuoteDB.created_at.desc()).first()
            
            if not db_quote:
                return None
            
            return Quote(
                id=db_quote.id,
                booking_request_id=db_quote.booking_request_id,
                price=db_quote.price,
                currency=db_quote.currency,
                description=db_quote.description,
                valid_until=db_quote.valid_until,
                status=db_quote.status,
                confirmed_at=db_quote.confirmed_at,
                confirmed_by_customer=db_quote.confirmed_by_customer,
                created_at=db_quote.created_at,
                updated_at=db_quote.updated_at
            )
        
        finally:
            session.close()
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by ID."""
        session = db_manager.get_session()
        
        try:
            db_customer = session.query(CustomerDB).filter(
                CustomerDB.id == customer_id
            ).first()
            
            if not db_customer:
                return None
            
            return Customer(
                id=db_customer.id,
                name=db_customer.name,
                email=db_customer.email,
                phone=db_customer.phone,
                company=db_customer.company,
                created_at=db_customer.created_at
            )
        
        finally:
            session.close()
    
    def get_all_booking_requests(self) -> List[dict]:
        """Get all booking requests with customer and quote information."""
        session = db_manager.get_session()
        
        try:
            requests = session.query(BookingRequestDB).order_by(
                BookingRequestDB.created_at.desc()
            ).all()
            
            result = []
            for request in requests:
                customer = session.query(CustomerDB).filter(
                    CustomerDB.id == request.customer_id
                ).first()
                
                quote = session.query(QuoteDB).filter(
                    QuoteDB.booking_request_id == request.id
                ).order_by(QuoteDB.created_at.desc()).first()
                
                result.append({
                    'request': request,
                    'customer': customer,
                    'quote': quote
                })
            
            return result
        
        finally:
            session.close()
    
    def get_pending_quotes(self) -> List[dict]:
        """Get all quotes that need customer confirmation."""
        session = db_manager.get_session()
        
        try:
            quotes = session.query(QuoteDB).filter(
                QuoteDB.status == QuoteStatus.SENT,
                QuoteDB.valid_until > datetime.utcnow()
            ).order_by(QuoteDB.created_at.desc()).all()
            
            result = []
            for quote in quotes:
                booking_request = session.query(BookingRequestDB).filter(
                    BookingRequestDB.id == quote.booking_request_id
                ).first()
                
                customer = None
                if booking_request:
                    customer = session.query(CustomerDB).filter(
                        CustomerDB.id == booking_request.customer_id
                    ).first()
                
                result.append({
                    'quote': quote,
                    'booking_request': booking_request,
                    'customer': customer
                })
            
            return result
        
        finally:
            session.close()


# Global booking service instance
booking_service = BookingService()