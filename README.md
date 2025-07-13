# Notion Processing AI Data Pipeline

An intelligent data pipeline that extracts, classifies, and summarizes documents from Notion databases using AI/LLM technology.

## Features

- **📥 Document Extraction**: Extract raw documents from Notion databases via API
- **🏷️ AI Classification**: Use LLM to classify documents into project/knowledge categories with sub-categories
- **📊 Weekly Summaries**: Generate comprehensive weekly reports of processed documents with mindset analysis
- **📈 Interactive Dashboard**: Streamlit-based dashboard for visualizing weekly summaries and trends
- **🗄️ Supabase Storage**: Store all data and processing results in Supabase (PostgreSQL)
- **🔄 Pipeline Orchestration**: Modular pipeline design for flexible processing
- **📈 Statistics & Monitoring**: Track processing status and statistics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Notion API    │───▶│   Extraction    │───▶│   Supabase      │
│   (Documents)   │    │   (Raw Data)    │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Classification  │    │   Statistics    │
                       │   (LLM/AI)      │    │   & Monitoring  │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Summarization │
                       │   (Weekly Reports)│
                       └─────────────────┘
```

## Document Classification

### Main Categories
- **PROJECT**: Documents related to project work, tasks, features, bugs, planning
- **KNOWLEDGE**: Documents containing knowledge, documentation, tutorials

### Sub-Categories

#### Project Sub-Categories
- `feature_request`: Requests for new features or functionality
- `bug_report`: Reports of bugs or issues
- `planning`: Project planning, roadmaps, timelines
- `research`: Research findings, analysis, investigations

#### Knowledge Sub-Categories
- `tutorial`: Step-by-step guides, how-to documents
- `reference`: Reference materials, documentation, specifications
- `best_practice`: Best practices, guidelines, standards
- `case_study`: Case studies, examples, success stories
- `documentation`: Technical documentation, API docs, etc.

## Mindset Analysis

The system now includes advanced mindset analysis capabilities that go beyond simple document classification to provide insights into your thinking patterns, interests, and mental state.

### Features

- **🧠 Content Analysis**: Analyzes document content to understand your interests and focus areas
- **📈 Pattern Recognition**: Identifies recurring themes and thinking patterns across your documents
- **🎯 Mindset Indicators**: Detects mindset characteristics like learning focus, project orientation, or research tendencies
- **📊 AI-Powered Insights**: Uses LLM to generate human-like insights about your cognitive patterns

### Mindset Analysis Methods

#### 1. Content-Based Analysis
- Analyzes the actual text content of your documents
- Identifies themes, topics, and writing patterns
- Provides insights into your current interests and focus areas

#### 2. Pattern Recognition
- Examines document types and categories for patterns
- Identifies dominant thinking modes (learning, project management, research, etc.)
- Tracks changes in focus over time

#### 3. AI-Generated Insights
- Uses OpenAI's GPT models to generate natural language insights
- Provides context-aware analysis of your mindset
- Offers personalized recommendations based on your patterns

### Usage Examples

```python
from notion_processing.summarizer import WeeklySummarizer

# Initialize summarizer
summarizer = WeeklySummarizer(api_key="your_openai_api_key")

# Get detailed mindset insights
insights = summarizer.get_mindset_insights()
print(f"Mindset indicators: {insights['mindset_indicators']}")

# Generate AI-powered weekly summary with mindset focus
summary = summarizer.run_weekly_summary()
print(f"AI Summary: {summary.summary_text}")
print(f"Key Insights: {summary.key_insights}")
```

### Mindset Indicators

The system can identify various mindset characteristics:

- **Learning Focus**: High concentration on educational content and skill development
- **Project Management**: Active engagement with planning and execution tasks
- **Research Orientation**: Analytical thinking and investigation patterns
- **Personal Reflection**: Strong self-awareness and introspective content
- **Creative Thinking**: Innovation-focused and idea-generation patterns

## Quick Start

### 1. Prerequisites

- Python 3.12+
- Supabase account and project
- Notion API token
- OpenAI API key
- [uv](https://docs.astral.sh/uv/) package manager

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd notion_processing

# Install dependencies with uv
uv sync

# Copy environment file
cp env.example .env
```

### 3. Database Setup

#### Option A: Supabase (Recommended)

1. **Create a Supabase project:**
   - Go to [https://supabase.com](https://supabase.com)
   - Sign up/login and create a new project
   - Wait for the project to be ready

2. **Get your connection string:**
   - Go to Project Settings > Database
   - Copy the 'Connection string' > 'URI'
   - It should look like: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`

3. **Test your connection:**
   ```bash
   python migrate_to_supabase.py --test
   ```

#### Option B: Local PostgreSQL (Development)

If you prefer to use local PostgreSQL for development:

```bash
# Uncomment the services in docker-compose.yml
# Start PostgreSQL and pgAdmin
docker-compose up -d

# The database will be available at:
# - PostgreSQL: localhost:5432
# - pgAdmin: http://localhost:8080 (admin@example.com / admin)
```

### 4. Configuration

Edit `.env` file with your credentials:
```bash
# Notion API Configuration
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
# For Supabase (recommended):
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# For local PostgreSQL (development):
# DATABASE_URL=postgresql://notion_user:notion_password@localhost:5432/notion_processing
```

### 5. Setup Database Tables

```bash
uv run python -m notion_processing.cli setup
```

### 6. Run the Pipeline

```bash
# Run complete pipeline
uv run python -m notion_processing.cli run

# Or run individual steps
uv run python -m notion_processing.cli extract --limit 10
uv run python -m notion_processing.cli classify
uv run python -m notion_processing.cli summarize
```

### 7. Setup Authentication (Optional)

The dashboard now includes Supabase authentication for secure access:

```bash
# Test authentication setup
python test_auth.py

# Configure authentication (see AUTHENTICATION_SETUP.md for details)
# 1. Set up Supabase project
# 2. Configure .streamlit/secrets.toml
# 3. Test the setup
```

### 8. View Dashboard

```bash
# Generate sample data for testing (optional)
make sample-data

# Start the interactive dashboard
make dashboard

# Or run directly with streamlit
uv run streamlit run streamlit_app.py

### 9. Run Mindset Analysis

```bash
# Run the mindset analysis example
uv run python example_mindset_analysis.py
```

This will generate both detailed mindset insights and AI-powered weekly summaries focused on understanding your thinking patterns and interests.
```

The dashboard will be available at `http://localhost:8501`

> **Note**: If authentication is enabled, you'll need to log in or create an account to access the dashboard.

> **Note**: If you don't have any weekly summaries yet, you can generate sample data using `make sample-data` to test the dashboard functionality.

## Dashboard

The interactive Streamlit dashboard provides comprehensive visualization and analysis of your weekly summaries.

### Features

- **📊 Overview Metrics**: Total weeks, documents, and averages
- **📈 Trend Analysis**: Charts showing document types and sub-categories over time
- **📋 Weekly Details**: Detailed view of each week's summary with:
  - Summary text and key insights
  - **📄 Document List**: View all documents used to create each summary
  - Document type and sub-category breakdowns
  - Interactive charts and visualizations
- **📋 Raw Data Table**: Exportable data table with all summary information
- **🔐 Authentication**: Secure login system with Supabase
- **📅 Date Filtering**: Filter summaries by date range

### Document List Feature

The dashboard now includes a comprehensive document list for each weekly summary:

- **Document Titles**: See the actual titles of all documents processed
- **Creation Dates**: View when each document was created
- **Last Edited**: Track when documents were last modified
- **Direct Links**: Click to open documents directly in Notion
- **Document Count**: See exactly how many documents contributed to each summary

This feature helps you understand exactly which documents influenced each weekly summary and provides transparency into the summarization process.

### Dashboard Sections

1. **Overview**: Key metrics and statistics
2. **Trends**: Interactive charts for document types, sub-categories, and total documents
3. **Weekly Details**: Detailed breakdown of selected weekly summaries
4. **Raw Data**: Tabular view with export functionality

### Running the Dashboard

```bash
# Using Makefile (recommended)
make dashboard

# Direct streamlit command
uv run streamlit run streamlit_app.py

# With custom port
uv run streamlit run streamlit_app.py --server.port 8502
```

## Migration from Local PostgreSQL to Supabase

If you're migrating from a local PostgreSQL setup to Supabase:

### Quick Migration

1. **Run the migration helper:**
   ```bash
   python migrate_to_supabase.py
   ```

2. **Follow the step-by-step instructions provided by the migration script**

3. **Test your connection:**
   ```bash
   python migrate_to_supabase.py --test
   ```

### Manual Migration Steps

1. **Create a Supabase project** at [https://supabase.com](https://supabase.com)

2. **Get your connection string** from Project Settings > Database > Connection string > URI

3. **Update your `.env` file:**
   ```bash
   # Replace your local DATABASE_URL with Supabase URL
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

4. **Test the connection:**
   ```bash
   uv run python -m notion_processing.cli setup
   ```

5. **Run your application** - tables will be created automatically

### Benefits of Supabase

- **No local database setup required**
- **Automatic backups and scaling**
- **Built-in authentication and real-time features**
- **Free tier available**
- **Production-ready infrastructure**

## Usage

### CLI Commands

```bash
# Show available commands
uv run python -m notion_processing.cli --help

# Run complete pipeline
uv run python -m notion_processing.cli run [--limit N] [--date YYYY-MM-DD]

# Extract documents only
uv run python -m notion_processing.cli extract [--limit N]

# Classify documents only
uv run python -m notion_processing.cli classify

# Generate weekly summary only
uv run python -m notion_processing.cli summarize [--date YYYY-MM-DD]

# Show processing statistics
uv run python -m notion_processing.cli stats

# Setup database tables
uv run python -m notion_processing.cli setup

# Show current configuration
uv run python -m notion_processing.cli config

# Run interactive dashboard
make dashboard
```

### Programmatic Usage

```python
from notion_processing.pipeline import NotionProcessingPipeline

# Initialize pipeline
pipeline = NotionProcessingPipeline()

# Setup database
pipeline.setup_database()

# Run complete pipeline
result = pipeline.run_full_pipeline(limit=10)

# Run individual steps
extracted_count = pipeline.run_extraction_only(limit=10)
classified_count = pipeline.run_classification_only()
summary = pipeline.run_summary_only()

# Get statistics
pipeline.display_processing_stats()
```

## Database Schema

### Tables

1. **notion_documents**: Raw documents from Notion
2. **document_classifications**: AI classification results
3. **weekly_summaries**: Generated weekly reports
4. **processing_records**: Processing status tracking

### Key Fields

- Document tracking with Notion IDs
- Classification confidence scores
- Processing timestamps
- Error handling and retry logic

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NOTION_TOKEN` | Notion integration token | Yes |
| `NOTION_DATABASE_ID` | Notion database ID | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `DATABASE_URL` | PostgreSQL connection URL | Yes |
| `LLM_MODEL` | LLM model for classification/summarization | No (default: gpt-4) |

### Notion Setup

1. Create a Notion integration at https://www.notion.so/my-integrations
2. Share your database with the integration
3. Get the database ID from the URL: `https://notion.so/workspace/{database_id}?v=...`

## Development

### Project Structure

```
notion_processing/
├── notion_processing/
│   ├── __init__.py
│   ├── models.py          # Data models and enums
│   ├── database.py        # Database configuration and models
│   ├── extractor.py       # Notion document extraction
│   ├── classifier.py      # LLM-based classification
│   ├── summarizer.py      # Weekly summary generation
│   ├── pipeline.py        # Main pipeline orchestrator
│   └── cli.py            # Command-line interface
├── tests/                 # Test suite
├── main.py               # Entry point
├── pyproject.toml        # Dependencies and project config
├── docker-compose.yml    # Database setup
├── env.example          # Environment variables template
├── Makefile             # Development commands
└── README.md            # This file
```

### Running Tests

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=notion_processing --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black notion_processing/ tests/
uv run isort notion_processing/ tests/

# Type checking
uv run mypy notion_processing/

# Linting
uv run flake8 notion_processing/ tests/
```

### Using Makefile

```bash
# Show all available commands
make help

# Complete development setup
make dev-setup

# Run quality checks
make quality

# Run tests
make test

# Format code
make format
```

## UV Package Management

This project uses [uv](https://docs.astral.sh/uv/) for fast Python package management:

```bash
# Add a new dependency
uv add package_name

# Add a development dependency
uv add --dev package_name

# Remove a dependency
uv remove package_name

# Update all dependencies
uv lock --upgrade

# Sync dependencies
uv sync
```

## Monitoring and Logging

The pipeline uses structured logging with `structlog`:

- JSON logging for production
- Console logging for development
- Error tracking and debugging information
- Processing statistics and metrics

## Error Handling

- Graceful handling of API rate limits
- Retry logic for transient failures
- Detailed error logging and reporting
- Processing status tracking

## Performance Considerations

- Batch processing for efficiency
- Rate limiting for API calls
- Database connection pooling
- Content length limits for LLM calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
1. Check the documentation
2. Review existing issues
3. Create a new issue with detailed information
