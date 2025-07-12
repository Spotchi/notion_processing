# Notion Processing AI Data Pipeline

An intelligent data pipeline that extracts, classifies, and summarizes documents from Notion databases using AI/LLM technology.

## Features

- **📥 Document Extraction**: Extract raw documents from Notion databases via API
- **🏷️ AI Classification**: Use LLM to classify documents into project/knowledge categories with sub-categories
- **📊 Weekly Summaries**: Generate comprehensive weekly reports of processed documents
- **🗄️ PostgreSQL Storage**: Store all data and processing results in PostgreSQL
- **🔄 Pipeline Orchestration**: Modular pipeline design for flexible processing
- **📈 Statistics & Monitoring**: Track processing status and statistics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Notion API    │───▶│   Extraction    │───▶│   PostgreSQL    │
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

## Quick Start

### 1. Prerequisites

- Python 3.12+
- PostgreSQL database
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

Using Docker Compose (recommended):
```bash
# Start PostgreSQL and pgAdmin
docker-compose up -d

# The database will be available at:
# - PostgreSQL: localhost:5432
# - pgAdmin: http://localhost:8080 (admin@example.com / admin)
```

Or using a local PostgreSQL instance:
```bash
# Create database
createdb notion_processing
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
DATABASE_URL=postgresql://notion_user:notion_password@localhost:5432/notion_processing
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
