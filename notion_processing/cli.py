"""Command-line interface for the Notion processing pipeline."""

import os
from datetime import datetime
from typing import Optional

import click
import structlog
from dotenv import load_dotenv

from .pipeline import NotionProcessingPipeline

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Notion Processing Pipeline CLI."""
    if verbose:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


@cli.command()
@click.option('--notion-token', envvar='NOTION_TOKEN', help='Notion API token')
@click.option('--notion-database-id', envvar='NOTION_DATABASE_ID', help='Notion database ID')
@click.option('--openai-api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
@click.option('--limit', type=int, help='Limit number of documents to extract')
@click.option('--date', type=click.DateTime(), help='Date for weekly summary (YYYY-MM-DD)')
def run(notion_token, notion_database_id, openai_api_key, database_url, limit, date):
    """Run the complete processing pipeline."""
    try:
        pipeline = NotionProcessingPipeline(
            notion_token=notion_token,
            notion_database_id=notion_database_id,
            openai_api_key=openai_api_key,
            database_url=database_url
        )
        
        # Setup database
        pipeline.setup_database()
        
        # Run full pipeline
        result = pipeline.run_full_pipeline(limit=limit, date=date)
        
        click.echo(f"\n✅ Pipeline completed successfully!")
        click.echo(f"📊 Extracted: {result['extracted_count']} documents")
        click.echo(f"🏷️  Classified: {result['classified_count']} documents")
        
    except Exception as e:
        click.echo(f"❌ Pipeline failed: {str(e)}", err=True)
        logger.error("Pipeline execution failed", error=str(e))
        raise click.Abort()


@cli.command()
@click.option('--notion-token', envvar='NOTION_TOKEN', help='Notion API token')
@click.option('--notion-database-id', envvar='NOTION_DATABASE_ID', help='Notion database ID')
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
@click.option('--limit', type=int, help='Limit number of documents to extract')
def extract(notion_token, notion_database_id, database_url, limit):
    """Extract documents from Notion database."""
    try:
        pipeline = NotionProcessingPipeline(
            notion_token=notion_token,
            notion_database_id=notion_database_id,
            database_url=database_url
        )
        
        # Setup database
        pipeline.setup_database()
        
        # Run extraction only
        count = pipeline.run_extraction_only(limit=limit)
        
        click.echo(f"✅ Extracted {count} documents from Notion")
        
    except Exception as e:
        click.echo(f"❌ Extraction failed: {str(e)}", err=True)
        logger.error("Extraction failed", error=str(e))
        raise click.Abort()


@cli.command()
@click.option('--openai-api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
@click.option('--model', default='gpt-4.1-mini-2025-04-14', help='LLM model to use for classification')
def classify(openai_api_key, database_url, model):
    """Classify extracted documents."""
    try:
        pipeline = NotionProcessingPipeline(
            openai_api_key=openai_api_key,
            database_url=database_url
        )
        
        # Run classification only
        count = pipeline.run_classification_only()
        
        click.echo(f"✅ Classified {count} documents")
        
    except Exception as e:
        click.echo(f"❌ Classification failed: {str(e)}", err=True)
        logger.error("Classification failed", error=str(e))
        raise click.Abort()


@cli.command()
@click.option('--openai-api-key', envvar='OPENAI_API_KEY', help='OpenAI API key')
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
@click.option('--date', type=click.DateTime(), help='Date for weekly summary (YYYY-MM-DD)')
@click.option('--model', default='gpt-4.1-mini-2025-04-14', help='LLM model to use for summarization')
def summarize(openai_api_key, database_url, date, model):
    """Generate weekly summary report."""
    try:
        pipeline = NotionProcessingPipeline(
            openai_api_key=openai_api_key,
            database_url=database_url
        )
        
        # Run summary only
        summary = pipeline.run_summary_only(date=date)
        
        click.echo(f"✅ Generated weekly summary for {summary['total_documents']} documents")
        click.echo(f"📅 Week: {summary['week_start'].strftime('%Y-%m-%d')} to {summary['week_end'].strftime('%Y-%m-%d')}")
        
    except Exception as e:
        click.echo(f"❌ Summary generation failed: {str(e)}", err=True)
        logger.error("Summary generation failed", error=str(e))
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
def stats(database_url):
    """Show processing statistics."""
    try:
        pipeline = NotionProcessingPipeline(database_url=database_url)
        pipeline.display_processing_stats()
        
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {str(e)}", err=True)
        logger.error("Failed to get statistics", error=str(e))
        raise click.Abort()


@cli.command()
@click.option('--database-url', envvar='DATABASE_URL', help='PostgreSQL database URL')
def setup(database_url):
    """Set up the database tables."""
    try:
        pipeline = NotionProcessingPipeline(database_url=database_url)
        pipeline.setup_database()
        
        click.echo("✅ Database tables created successfully")
        
    except Exception as e:
        click.echo(f"❌ Database setup failed: {str(e)}", err=True)
        logger.error("Database setup failed", error=str(e))
        raise click.Abort()


@cli.command()
def config():
    """Show current configuration."""
    click.echo("🔧 Current Configuration:")
    click.echo(f"   Notion Token: {'✅ Set' if os.getenv('NOTION_TOKEN') else '❌ Not set'}")
    click.echo(f"   Notion Database ID: {'✅ Set' if os.getenv('NOTION_DATABASE_ID') else '❌ Not set'}")
    click.echo(f"   OpenAI API Key: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    click.echo(f"   Database URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'}")
    
    if os.getenv('NOTION_DATABASE_ID'):
        click.echo(f"   Database ID: {os.getenv('NOTION_DATABASE_ID')}")
    if os.getenv('DATABASE_URL'):
        db_url = os.getenv('DATABASE_URL')
        # Mask password in URL
        if '@' in db_url:
            parts = db_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                if len(user_pass) >= 3:
                    masked_url = f"{user_pass[0]}:***@{parts[1]}"
                    click.echo(f"   Database URL: {masked_url}")
                else:
                    click.echo(f"   Database URL: {db_url}")
            else:
                click.echo(f"   Database URL: {db_url}")
        else:
            click.echo(f"   Database URL: {db_url}")


if __name__ == '__main__':
    cli() 