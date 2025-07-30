"""Streamlit application for viewing weekly summaries."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from st_supabase_connection import SupabaseConnection

from plotly.subplots import make_subplots

from notion_processing.database import WeeklySummaryDB, db_manager, NotionDocumentDB
from notion_processing.models import WeeklySummary


def init_authentication():
    """Initialize authentication state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False
    if 'show_password_reset' not in st.session_state:
        st.session_state.show_password_reset = False


def login_form(conn):
    """Display login form."""
    st.title("🔐 Login")
    st.markdown("Please log in to access the Weekly Summaries Dashboard.")
    
    # Add some styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .auth-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a centered container for the login form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit_button = st.form_submit_button("Login")
                
                if submit_button:
                    if email and password:
                        with st.spinner("Logging in..."):
                            try:
                                # Attempt to sign in with Supabase
                                result = conn.auth.sign_in_with_password({
                                    "email": email,
                                    "password": password
                                })
                                
                                if result.user:
                                    st.session_state.authenticated = True
                                    st.session_state.user_email = result.user.email
                                    st.session_state.user_id = result.user.id
                                    st.success("Login successful!")
                                    st.rerun()
                                else:
                                    st.error("Login failed. Please check your credentials.")
                            except Exception as e:
                                error_msg = str(e)
                                if "Invalid login credentials" in error_msg:
                                    st.error("Invalid email or password. Please try again.")
                                elif "Email not confirmed" in error_msg:
                                    st.error("Please verify your email address before logging in.")
                                else:
                                    st.error(f"Login error: {error_msg}")
                    else:
                        st.error("Please enter both email and password.")
            
            # Additional options
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Sign Up"):
                    st.session_state.show_signup = True
                    st.rerun()
            with col2:
                if st.button("Forgot Password?"):
                    st.session_state.show_password_reset = True
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)


def signup_form(conn):
    """Display signup form."""
    st.title("📝 Sign Up")
    st.markdown("Create a new account to access the Weekly Summaries Dashboard.")
    
    # Create a centered container for the signup form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            with st.form("signup_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                submit_button = st.form_submit_button("Sign Up")
                
                if submit_button:
                    if email and password and confirm_password:
                        if password == confirm_password:
                            if len(password) >= 6:
                                with st.spinner("Creating account..."):
                                    try:
                                        # Attempt to sign up with Supabase
                                        result = conn.auth.sign_up({
                                            "email": email,
                                            "password": password
                                        })
                                        
                                        if result.user:
                                            st.success("Account created successfully! Please check your email for verification.")
                                            st.session_state.show_signup = False
                                            st.rerun()
                                        else:
                                            st.error("Sign up failed. Please try again.")
                                    except Exception as e:
                                        error_msg = str(e)
                                        if "User already registered" in error_msg:
                                            st.error("An account with this email already exists. Please try logging in instead.")
                                        elif "Password should be at least" in error_msg:
                                            st.error("Password must be at least 6 characters long.")
                                        else:
                                            st.error(f"Sign up error: {error_msg}")
                            else:
                                st.error("Password must be at least 6 characters long.")
                        else:
                            st.error("Passwords do not match.")
                    else:
                        st.error("Please fill in all fields.")
            
            # Back to login link
            st.markdown("---")
            st.markdown("Already have an account?")
            if st.button("Back to Login"):
                st.session_state.show_signup = False
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)


def logout_button():
    """Display logout button in sidebar."""
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_id = None
        st.rerun()


def show_user_info():
    """Display user information in sidebar."""
    if st.session_state.authenticated:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Info")
        st.sidebar.markdown(f"**Email:** {st.session_state.user_email}")
        st.sidebar.markdown(f"**User ID:** {st.session_state.user_id[:8]}...")


def password_reset_form(conn):
    """Display password reset form."""
    st.title("🔑 Password Reset")
    st.markdown("Enter your email to receive a password reset link.")
    
    # Create a centered container for the password reset form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.container():
                st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            with st.form("password_reset_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                submit_button = st.form_submit_button("Send Reset Link")
                
                if submit_button:
                    if email:
                        with st.spinner("Sending reset email..."):
                            try:
                                # Attempt to send password reset email
                                result = conn.auth.reset_password_email({
                                    "email": email
                                })
                                
                                if result:
                                    st.success("Password reset email sent! Please check your inbox.")
                                    st.session_state.show_password_reset = False
                                    st.rerun()
                                else:
                                    st.error("Failed to send reset email. Please try again.")
                            except Exception as e:
                                error_msg = str(e)
                                if "User not found" in error_msg:
                                    st.error("No account found with this email address.")
                                else:
                                    st.error(f"Password reset error: {error_msg}")
                    else:
                        st.error("Please enter your email address.")
            
            # Back to login link
            st.markdown("---")
            if st.button("Back to Login"):
                st.session_state.show_password_reset = False
                st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)


def load_weekly_summaries() -> List[WeeklySummary]:
    """Load all weekly summaries from the database."""
    session = db_manager.get_session()
    
    try:
        db_summaries = session.query(WeeklySummaryDB).order_by(
            WeeklySummaryDB.week_start.desc()
        ).all()
        
        summaries = []
        for db_summary in db_summaries:
            # Parse JSON fields
            documents_by_type = json.loads(db_summary.documents_by_type) if db_summary.documents_by_type else {}
            documents_by_subcategory = json.loads(db_summary.documents_by_subcategory) if db_summary.documents_by_subcategory else {}
            key_insights = json.loads(db_summary.key_insights) if db_summary.key_insights else []
            
            summary = WeeklySummary(
                week_start=db_summary.week_start,
                week_end=db_summary.week_end,
                total_documents=db_summary.total_documents,
                documents_by_type=documents_by_type,
                documents_by_subcategory=documents_by_subcategory,
                summary_text=db_summary.summary_text,
                key_insights=key_insights,
                generated_at=db_summary.generated_at
            )
            summaries.append(summary)
        
        return summaries
    
    except Exception as e:
        st.error(f"Error loading weekly summaries: {str(e)}")
        return []
    finally:
        session.close()


def get_documents_by_date_range(week_start: datetime, week_end: datetime) -> List[dict]:
    """Get documents from the database for a specific date range."""
    session = db_manager.get_session()
    
    try:
        # Query documents created within the date range
        documents = session.query(NotionDocumentDB).filter(
            NotionDocumentDB.created_time >= week_start,
            NotionDocumentDB.created_time <= week_end
        ).order_by(NotionDocumentDB.created_time.desc()).all()
        
        document_details = []
        for doc in documents:
            document_details.append({
                'id': doc.id,
                'title': doc.title,
                'url': doc.url,
                'created_time': doc.created_time,
                'last_edited_time': doc.last_edited_time
            })
        
        return document_details
    
    except Exception as e:
        st.error(f"Error loading documents by date range: {str(e)}")
        return []
    finally:
        session.close()


def create_document_type_chart(summaries: List[WeeklySummary]) -> go.Figure:
    """Create a chart showing document types over time."""
    data = []
    for summary in summaries:
        for doc_type, count in summary.documents_by_type.items():
            data.append({
                'Week': summary.week_start.strftime('%Y-%m-%d'),
                'Document Type': doc_type,
                'Count': count
            })
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    fig = px.bar(
        df, 
        x='Week', 
        y='Count', 
        color='Document Type',
        title='Document Types by Week',
        barmode='stack'
    )
    fig.update_layout(
        xaxis_title="Week Starting",
        yaxis_title="Number of Documents",
        height=400
    )
    return fig


def create_subcategory_chart(summaries: List[WeeklySummary]) -> go.Figure:
    """Create a chart showing sub-categories over time."""
    data = []
    for summary in summaries:
        for subcategory, count in summary.documents_by_subcategory.items():
            data.append({
                'Week': summary.week_start.strftime('%Y-%m-%d'),
                'Sub-category': subcategory,
                'Count': count
            })
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    fig = px.bar(
        df, 
        x='Week', 
        y='Count', 
        color='Sub-category',
        title='Document Sub-categories by Week',
        barmode='stack'
    )
    fig.update_layout(
        xaxis_title="Week Starting",
        yaxis_title="Number of Documents",
        height=400
    )
    return fig


def create_total_documents_trend(summaries: List[WeeklySummary]) -> go.Figure:
    """Create a line chart showing total documents trend."""
    data = []
    for summary in summaries:
        data.append({
            'Week': summary.week_start.strftime('%Y-%m-%d'),
            'Total Documents': summary.total_documents
        })
    
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    fig = px.line(
        df, 
        x='Week', 
        y='Total Documents',
        title='Total Documents Processed by Week',
        markers=True
    )
    fig.update_layout(
        xaxis_title="Week Starting",
        yaxis_title="Total Documents",
        height=400
    )
    return fig


def display_summary_details(summary: WeeklySummary):
    """Display detailed information for a selected summary."""
    st.subheader(f"Week of {summary.week_start.strftime('%B %d, %Y')}")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Documents", summary.total_documents)
    with col2:
        st.metric("Document Types", len(summary.documents_by_type))
    with col3:
        st.metric("Sub-categories", len(summary.documents_by_subcategory))
    with col4:
        st.metric("Generated", summary.generated_at.strftime('%Y-%m-%d'))
    
    # Summary text
    st.subheader("Summary")
    st.write(summary.summary_text)
    
    # Key insights
    if summary.key_insights:
        st.subheader("Key Insights")
        for i, insight in enumerate(summary.key_insights, 1):
            st.write(f"{i}. {insight}")
    
    # Document list
    st.subheader("📄 Documents in This Week")
    st.markdown("Querying documents by date range...")
    
    with st.spinner("Loading documents for this week..."):
        document_details = get_documents_by_date_range(summary.week_start, summary.week_end)
    
    if document_details:
        st.markdown(f"Found **{len(document_details)}** documents created during this week.")
        
        # Create a DataFrame for the documents
        doc_df = pd.DataFrame(document_details)
        doc_df['created_time'] = pd.to_datetime(doc_df['created_time']).dt.strftime('%Y-%m-%d %H:%M')
        doc_df['last_edited_time'] = pd.to_datetime(doc_df['last_edited_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Display documents with clickable titles using markdown
        st.markdown("### Documents")
        
        for _, doc in doc_df.iterrows():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"[**{doc['title']}**]({doc['url']})")
            with col2:
                st.caption(f"Created: {doc['created_time']}")
            with col3:
                st.caption(f"Edited: {doc['last_edited_time']}")
            st.markdown("")
    
    # Document type breakdown
    if summary.documents_by_type:
        st.subheader("Document Types")
        doc_type_df = pd.DataFrame([
            {'Type': k, 'Count': v} 
            for k, v in summary.documents_by_type.items()
        ])
        st.dataframe(doc_type_df, use_container_width=True)
        
        # Pie chart for document types
        fig = px.pie(
            doc_type_df, 
            values='Count', 
            names='Type',
            title='Document Type Distribution'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Sub-category breakdown
    if summary.documents_by_subcategory:
        st.subheader("Sub-categories")
        subcat_df = pd.DataFrame([
            {'Sub-category': k, 'Count': v} 
            for k, v in summary.documents_by_subcategory.items()
        ])
        st.dataframe(subcat_df, use_container_width=True)
        
        # Bar chart for sub-categories
        fig = px.bar(
            subcat_df, 
            x='Sub-category', 
            y='Count',
            title='Sub-category Distribution'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Main Streamlit application."""
    
    conn = st.connection("supabase",type=SupabaseConnection)

    st.set_page_config(
        page_title="CHB Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize authentication
    init_authentication()
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        # Show appropriate form based on state
        if st.session_state.get('show_signup', False):
            signup_form(conn)
        elif st.session_state.get('show_password_reset', False):
            password_reset_form(conn)
        else:
            # Show login form
            login_form(conn)
        return
    
    # User is authenticated - show dashboard
    # Sidebar navigation
    st.sidebar.title("CHB Dashboard")
    
    # Navigation menu
    page = st.sidebar.selectbox(
        "Select Page",
        ["Weekly Summaries", "Booking System", "Admin Panel"]
    )
    
    # Show user info and logout button in sidebar
    show_user_info()
    logout_button()
    
    if page == "Weekly Summaries":
        show_weekly_summaries()
    elif page == "Booking System":
        show_booking_system()
    elif page == "Admin Panel":
        show_admin_panel()


def show_weekly_summaries():
    """Show the weekly summaries dashboard."""
    st.title("📊 Weekly Summaries Dashboard")
    st.markdown("View and analyze weekly summaries of processed Notion documents.")
    
    # Information about new features
    st.info("💡 **New Feature**: You can now view the list of documents for each weekly summary. The system queries documents by date range to show you what was processed during each week.")
    
    # Load data
    with st.spinner("Loading weekly summaries..."):
        summaries = load_weekly_summaries()
    
    if not summaries:
        st.warning("No weekly summaries found in the database.")
        st.info("Make sure you have generated weekly summaries using the summarizer.")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    min_date = min(s.week_start for s in summaries)
    max_date = max(s.week_start for s in summaries)
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_summaries = [
            s for s in summaries 
            if start_date <= s.week_start.date() <= end_date
        ]
    else:
        filtered_summaries = summaries
    
    # Overview metrics
    st.header("📈 Overview")
    total_weeks = len(filtered_summaries)
    total_docs = sum(s.total_documents for s in filtered_summaries)
    avg_docs_per_week = total_docs / total_weeks if total_weeks > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Weeks", total_weeks)
    with col2:
        st.metric("Total Documents", total_docs)
    with col3:
        st.metric("Avg Docs/Week", f"{avg_docs_per_week:.1f}")
    with col4:
        st.metric("Date Range", f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
    
    # Charts
    st.header("📊 Trends")
    
    # Create tabs for different charts
    tab1, tab2, tab3 = st.tabs(["Document Types", "Sub-categories", "Total Documents"])
    
    with tab1:
        fig = create_document_type_chart(filtered_summaries)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No document type data available for the selected date range.")
    
    with tab2:
        fig = create_subcategory_chart(filtered_summaries)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sub-category data available for the selected date range.")
    
    with tab3:
        fig = create_total_documents_trend(filtered_summaries)
        if fig.data:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No total documents data available for the selected date range.")
    
    # Detailed view
    st.header("📋 Weekly Details")
    
    if filtered_summaries:
        # Create a selectbox for choosing a specific week
        week_options = [
            f"{s.week_start.strftime('%B %d, %Y')} ({s.total_documents} docs)"
            for s in filtered_summaries
        ]
        
        selected_week = st.selectbox(
            "Select a week to view details:",
            options=week_options,
            index=0
        )
        
        # Find the selected summary
        selected_index = week_options.index(selected_week)
        selected_summary = filtered_summaries[selected_index]
        
        # Display the selected summary
        display_summary_details(selected_summary)
    else:
        st.info("No summaries available for the selected date range.")
    
    # Raw data table
    st.header("📋 Raw Data")
    
    if filtered_summaries:
        # Create a DataFrame for the table
        table_data = []
        for summary in filtered_summaries:
            table_data.append({
                'Week Start': summary.week_start.strftime('%Y-%m-%d'),
                'Week End': summary.week_end.strftime('%Y-%m-%d'),
                'Total Documents': summary.total_documents,
                'Document Types': len(summary.documents_by_type),
                'Sub-categories': len(summary.documents_by_subcategory),
                'Generated': summary.generated_at.strftime('%Y-%m-%d %H:%M'),
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"weekly_summaries_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No data available for the selected date range.")


def show_booking_system():
    """Show the booking system interface."""
    from .booking_service import booking_service
    
    st.title("📅 CHB Booking System")
    st.markdown("Request services and manage quotes from CHB.")
    
    # Tab selection
    tab1, tab2, tab3 = st.tabs(["New Booking Request", "My Quotes", "Quote Confirmation"])
    
    with tab1:
        show_new_booking_form()
    
    with tab2:
        show_customer_quotes()
    
    with tab3:
        show_quote_confirmation()


def show_new_booking_form():
    """Show the new booking request form."""
    from .booking_service import booking_service
    
    st.header("📝 New Booking Request")
    st.markdown("Fill out the form below to request a service from CHB.")
    
    with st.form("booking_request_form"):
        # Customer information
        st.subheader("Customer Information")
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Full Name *", placeholder="Enter your full name")
            customer_email = st.text_input("Email Address *", placeholder="Enter your email")
        
        with col2:
            customer_phone = st.text_input("Phone Number", placeholder="Enter your phone number")
            customer_company = st.text_input("Company", placeholder="Enter your company (optional)")
        
        # Service details
        st.subheader("Service Details")
        service_type = st.selectbox(
            "Service Type *",
            ["Consulting", "Development", "Maintenance", "Training", "Other"]
        )
        
        description = st.text_area(
            "Service Description *",
            placeholder="Please describe your requirements in detail...",
            height=150
        )
        
        col3, col4 = st.columns(2)
        with col3:
            preferred_date = st.date_input("Preferred Date", value=None)
        
        with col4:
            location = st.text_input("Location", placeholder="Service location (if applicable)")
        
        # Submit button
        submitted = st.form_submit_button("Submit Booking Request", type="primary")
        
        if submitted:
            if not customer_name or not customer_email or not description:
                st.error("Please fill in all required fields (*)")
            else:
                try:
                    # Create or get customer
                    customer = booking_service.create_customer(
                        name=customer_name,
                        email=customer_email,
                        phone=customer_phone,
                        company=customer_company
                    )
                    
                    # Create booking request
                    booking_request = booking_service.create_booking_request(
                        customer_id=customer.id,
                        service_type=service_type,
                        description=description,
                        preferred_date=datetime.combine(preferred_date, datetime.min.time()) if preferred_date else None,
                        location=location
                    )
                    
                    st.success(f"✅ Booking request submitted successfully! Request ID: {booking_request.id}")
                    st.info("CHB will review your request and provide a quote within 24 hours.")
                    
                    # Store the request ID in session state for easy access
                    st.session_state.last_booking_request_id = booking_request.id
                    
                except Exception as e:
                    st.error(f"Error submitting booking request: {str(e)}")


def show_customer_quotes():
    """Show quotes for the current customer."""
    from .booking_service import booking_service
    
    st.header("💰 My Quotes")
    st.markdown("View quotes for your booking requests.")
    
    # Get email from user input for demo purposes
    # In a real application, this would be tied to the authenticated user
    customer_email = st.text_input("Enter your email to view quotes:", placeholder="your.email@example.com")
    
    if customer_email:
        # Find customer by email
        session = db_manager.get_session()
        try:
            from .database import CustomerDB
            customer = session.query(CustomerDB).filter(
                CustomerDB.email == customer_email
            ).first()
            
            if customer:
                # Get booking requests for this customer
                from .database import BookingRequestDB, QuoteDB
                booking_requests = session.query(BookingRequestDB).filter(
                    BookingRequestDB.customer_id == customer.id
                ).order_by(BookingRequestDB.created_at.desc()).all()
                
                if booking_requests:
                    for request in booking_requests:
                        with st.expander(f"Request #{request.id} - {request.service_type} ({request.status.value})"):
                            st.write(f"**Description:** {request.description}")
                            st.write(f"**Requested:** {request.created_at.strftime('%Y-%m-%d %H:%M')}")
                            if request.preferred_date:
                                st.write(f"**Preferred Date:** {request.preferred_date.strftime('%Y-%m-%d')}")
                            if request.location:
                                st.write(f"**Location:** {request.location}")
                            
                            # Get quote for this request
                            quote = session.query(QuoteDB).filter(
                                QuoteDB.booking_request_id == request.id
                            ).order_by(QuoteDB.created_at.desc()).first()
                            
                            if quote:
                                st.write(f"**Quote:** {quote.currency} {quote.price:,.2f}")
                                st.write(f"**Quote Description:** {quote.description}")
                                st.write(f"**Valid Until:** {quote.valid_until.strftime('%Y-%m-%d %H:%M')}")
                                st.write(f"**Status:** {quote.status.value}")
                                
                                if quote.status.value == "sent" and quote.valid_until > datetime.utcnow():
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button(f"✅ Confirm Quote #{quote.id}", key=f"confirm_{quote.id}"):
                                            if booking_service.confirm_quote(quote.id, True):
                                                st.success("Quote confirmed successfully!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to confirm quote.")
                                    
                                    with col2:
                                        if st.button(f"❌ Reject Quote #{quote.id}", key=f"reject_{quote.id}"):
                                            if booking_service.confirm_quote(quote.id, False):
                                                st.success("Quote rejected.")
                                                st.rerun()
                                            else:
                                                st.error("Failed to reject quote.")
                            else:
                                st.info("No quote available yet. CHB will provide a quote soon.")
                else:
                    st.info("No booking requests found for this email.")
            else:
                st.warning("No customer found with this email address.")
        
        finally:
            session.close()


def show_quote_confirmation():
    """Show pending quotes that need confirmation."""
    st.header("🔔 Quote Confirmation")
    st.markdown("Confirm or reject quotes for your services.")
    
    # For demo purposes, show a sample quote that needs confirmation
    st.info("💡 This section shows quotes that are waiting for customer confirmation.")
    
    from .booking_service import booking_service
    
    # Get pending quotes
    pending_quotes = booking_service.get_pending_quotes()
    
    if pending_quotes:
        st.write(f"**{len(pending_quotes)} quotes awaiting customer confirmation:**")
        
        for item in pending_quotes:
            quote = item['quote']
            booking_request = item['booking_request']
            customer = item['customer']
            
            with st.expander(f"Quote #{quote.id} for {customer.name if customer else 'Unknown'} - {quote.currency} {quote.price:,.2f}"):
                if customer:
                    st.write(f"**Customer:** {customer.name} ({customer.email})")
                if booking_request:
                    st.write(f"**Service:** {booking_request.service_type}")
                    st.write(f"**Description:** {booking_request.description}")
                
                st.write(f"**Quote Amount:** {quote.currency} {quote.price:,.2f}")
                st.write(f"**Quote Description:** {quote.description}")
                st.write(f"**Valid Until:** {quote.valid_until.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Status:** {quote.status.value}")
                
                # Show time remaining
                time_remaining = quote.valid_until - datetime.utcnow()
                if time_remaining.days > 0:
                    st.write(f"**Time Remaining:** {time_remaining.days} days")
                else:
                    st.write(f"**Time Remaining:** {time_remaining.seconds // 3600} hours")
                
                st.markdown("**Customer needs to confirm this quote to proceed with the booking.**")
    else:
        st.info("No pending quotes at the moment.")


def show_admin_panel():
    """Show the admin panel for managing bookings and quotes."""
    st.title("🔧 Admin Panel")
    st.markdown("Manage booking requests and create quotes.")
    
    # Only show admin panel to authenticated users (in a real app, check for admin role)
    tab1, tab2 = st.tabs(["Booking Requests", "Create Quote"])
    
    with tab1:
        show_admin_booking_requests()
    
    with tab2:
        show_admin_create_quote()


def show_admin_booking_requests():
    """Show all booking requests for admin review."""
    from .booking_service import booking_service
    
    st.header("📋 All Booking Requests")
    
    # Get all booking requests
    all_requests = booking_service.get_all_booking_requests()
    
    if all_requests:
        for item in all_requests:
            request = item['request']
            customer = item['customer']
            quote = item['quote']
            
            with st.expander(f"Request #{request.id} - {customer.name if customer else 'Unknown'} ({request.status.value})"):
                if customer:
                    st.write(f"**Customer:** {customer.name}")
                    st.write(f"**Email:** {customer.email}")
                    if customer.phone:
                        st.write(f"**Phone:** {customer.phone}")
                    if customer.company:
                        st.write(f"**Company:** {customer.company}")
                
                st.write(f"**Service Type:** {request.service_type}")
                st.write(f"**Description:** {request.description}")
                st.write(f"**Requested:** {request.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                if request.preferred_date:
                    st.write(f"**Preferred Date:** {request.preferred_date.strftime('%Y-%m-%d')}")
                if request.location:
                    st.write(f"**Location:** {request.location}")
                
                if quote:
                    st.write(f"**Current Quote:** {quote.currency} {quote.price:,.2f}")
                    st.write(f"**Quote Status:** {quote.status.value}")
                    if quote.confirmed_by_customer:
                        st.success("✅ Quote confirmed by customer")
                else:
                    st.info("No quote created yet")
    else:
        st.info("No booking requests found.")


def show_admin_create_quote():
    """Show form for creating quotes."""
    from .booking_service import booking_service
    
    st.header("💰 Create Quote")
    st.markdown("Create a quote for a booking request.")
    
    # Get all pending booking requests (without quotes)
    session = db_manager.get_session()
    try:
        from .database import BookingRequestDB, QuoteDB
        
        # Get requests that don't have quotes yet or need new quotes
        requests_without_quotes = session.query(BookingRequestDB).filter(
            BookingRequestDB.status.in_(['pending', 'quoted'])
        ).all()
        
        if requests_without_quotes:
            # Create selectbox options
            request_options = {}
            for req in requests_without_quotes:
                from .database import CustomerDB
                customer = session.query(CustomerDB).filter(
                    CustomerDB.id == req.customer_id
                ).first()
                
                customer_name = customer.name if customer else "Unknown"
                option_text = f"Request #{req.id} - {customer_name} - {req.service_type}"
                request_options[option_text] = req.id
            
            selected_request = st.selectbox(
                "Select Booking Request:",
                options=list(request_options.keys())
            )
            
            if selected_request:
                request_id = request_options[selected_request]
                
                # Show request details
                request = session.query(BookingRequestDB).filter(
                    BookingRequestDB.id == request_id
                ).first()
                
                if request:
                    st.subheader("Request Details")
                    st.write(f"**Service Type:** {request.service_type}")
                    st.write(f"**Description:** {request.description}")
                    
                    # Quote form
                    with st.form("create_quote_form"):
                        st.subheader("Create Quote")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
                            currency = st.selectbox("Currency", ["USD", "EUR", "GBP"])
                        
                        with col2:
                            validity_days = st.number_input("Valid for (days)", min_value=1, max_value=90, value=30)
                        
                        quote_description = st.text_area(
                            "Quote Description",
                            placeholder="Describe what is included in this quote...",
                            height=100
                        )
                        
                        submitted = st.form_submit_button("Create Quote", type="primary")
                        
                        if submitted:
                            if price > 0 and quote_description:
                                try:
                                    quote = booking_service.create_quote(
                                        booking_request_id=request_id,
                                        price=price,
                                        description=quote_description,
                                        currency=currency,
                                        validity_days=validity_days
                                    )
                                    
                                    st.success(f"✅ Quote created successfully! Quote ID: {quote.id}")
                                    st.info("The customer will be notified and can now confirm or reject the quote.")
                                    
                                except Exception as e:
                                    st.error(f"Error creating quote: {str(e)}")
                            else:
                                st.error("Please enter a valid price and description.")
        else:
            st.info("No pending booking requests found.")
    
    finally:
        session.close()


if __name__ == "__main__":
    main() 