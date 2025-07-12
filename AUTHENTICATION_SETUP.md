# Authentication Setup Guide

This guide explains how to set up Supabase authentication for the Weekly Summaries Dashboard.

## Prerequisites

1. A Supabase project (you can create one at [supabase.com](https://supabase.com))
2. The `st-supabase-connection` package (already included in dependencies)

## Configuration Steps

### 1. Supabase Project Setup

1. Go to your Supabase project dashboard
2. Navigate to **Authentication** > **Settings**
3. Configure the following settings:
   - **Site URL**: Set to your Streamlit app URL (e.g., `http://localhost:8501` for local development)
   - **Redirect URLs**: Add your app URL
   - **Email Templates**: Customize if desired

### 2. Environment Configuration

The app is already configured to use Supabase through Streamlit's secrets management. The configuration is in `.streamlit/secrets.toml`:

```toml
[connections.supabase]
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_KEY = "your_supabase_anon_key"
```

### 3. Database Setup

Make sure your Supabase database has the required tables for weekly summaries. The app will automatically create users through Supabase's built-in authentication system.

### 4. Running the App

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

## Features

The authentication system includes:

- **Login**: Email/password authentication
- **Sign Up**: New user registration with email verification
- **Password Reset**: Email-based password reset functionality
- **Session Management**: Automatic session persistence
- **User Info Display**: Shows logged-in user information in sidebar

## User Management

### Creating Users

Users can sign up directly through the app interface. New users will receive an email verification link.

### Admin Functions

For admin functions, you can:
1. Use the Supabase dashboard to manage users
2. Access the **Authentication** > **Users** section
3. Manually create, edit, or delete users as needed

## Security Considerations

- All authentication is handled by Supabase's secure authentication system
- Passwords are never stored in plain text
- Sessions are managed securely
- Email verification is required for new accounts

## Troubleshooting

### Common Issues

1. **"Login failed" error**: Check that the user exists and email is verified
2. **"Sign up failed" error**: Ensure email is not already registered
3. **Connection errors**: Verify Supabase URL and key in secrets.toml

### Debug Mode

To enable debug mode, add this to your Streamlit app:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After setting up authentication, you can:

1. Customize the UI/UX of the authentication forms
2. Add role-based access control
3. Implement additional security measures
4. Add social login providers (Google, GitHub, etc.) 