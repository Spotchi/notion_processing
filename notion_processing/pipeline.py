"""Main pipeline orchestrator for the Notion processing system."""

import os
from datetime import datetime
from typing import Optional

import structlog
from rich.console import Console
from rich.table import Table

from .classifier import DocumentClassifier
from .database import db_manager
from .extractor import NotionExtractor
from .summarizer import WeeklySummarizer

logger = structlog.get_logger(__name__)
console = Console()


class NotionProcessingPipeline:
    """Main pipeline for processing Notion documents."""
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        notion_database_id: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        database_url: Optional[str] = None,
        llm_model: str = "gpt-4"
    ):
        """Initialize the processing pipeline."""
        self.notion_token = notion_token or os.getenv("NOTION_TOKEN")
        self.notion_database_id = notion_database_id or os.getenv("NOTION_DATABASE_ID")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.llm_model = llm_model
        
        # Validate required environment variables
        if not self.notion_token:
            raise ValueError("Notion token is required. Set NOTION_TOKEN environment variable.")
        if not self.notion_database_id:
            raise ValueError("Notion database ID is required. Set NOTION_DATABASE_ID environment variable.")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Initialize components
        self.extractor = NotionExtractor(self.notion_token, self.notion_database_id)
        self.classifier = DocumentClassifier(self.openai_api_key, self.llm_model)
        self.summarizer = WeeklySummarizer(self.openai_api_key, self.llm_model)
        
        # Initialize database
        if self.database_url:
            db_manager.engine = db_manager.engine.execution_options(url=self.database_url)
        
        logger.info("Notion processing pipeline initialized")
    
    def setup_database(self):
        """Set up the database tables."""
        try:
            db_manager.create_tables()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def run_extraction_step(self, limit: Optional[int] = None) -> int:
        """Run the document extraction step."""
        console.print("[bold blue]Step 1: Extracting documents from Notion[/bold blue]")
        
        try:
            documents = self.extractor.run_extraction(limit=limit)
            console.print(f"[green]✓ Extracted {len(documents)} documents[/green]")
            return len(documents)
        
        except Exception as e:
            console.print(f"[red]✗ Extraction failed: {str(e)}[/red]")
            logger.error("Extraction step failed", error=str(e))
            raise
    
    def run_classification_step(self) -> int:
        """Run the document classification step."""
        console.print("[bold blue]Step 2: Classifying documents[/bold blue]")
        
        try:
            classifications = self.classifier.run_classification()
            console.print(f"[green]✓ Classified {len(classifications)} documents[/green]")
            return len(classifications)
        
        except Exception as e:
            console.print(f"[red]✗ Classification failed: {str(e)}[/red]")
            logger.error("Classification step failed", error=str(e))
            raise
    
    def run_summary_step(self, date: Optional[datetime] = None) -> dict:
        """Run the weekly summary step."""
        console.print("[bold blue]Step 3: Generating weekly summary[/bold blue]")
        
        try:
            summary = self.summarizer.run_weekly_summary(date)
            console.print(f"[green]✓ Generated weekly summary for {summary.total_documents} documents[/green]")
            return {
                "week_start": summary.week_start,
                "week_end": summary.week_end,
                "total_documents": summary.total_documents,
                "summary_text": summary.summary_text,
                "key_insights": summary.key_insights
            }
        
        except Exception as e:
            console.print(f"[red]✗ Summary generation failed: {str(e)}[/red]")
            logger.error("Summary step failed", error=str(e))
            raise
    
    def display_summary_report(self, summary_data: dict):
        """Display the weekly summary report in a formatted table."""
        console.print("\n[bold yellow]Weekly Summary Report[/bold yellow]")
        
        # Create summary table
        summary_table = Table(title="Weekly Processing Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Week Start", summary_data["week_start"].strftime("%Y-%m-%d"))
        summary_table.add_row("Week End", summary_data["week_end"].strftime("%Y-%m-%d"))
        summary_table.add_row("Total Documents", str(summary_data["total_documents"]))
        
        console.print(summary_table)
        
        # Display summary text
        console.print("\n[bold]Summary:[/bold]")
        console.print(summary_data["summary_text"])
        
        # Display key insights
        if summary_data["key_insights"]:
            console.print("\n[bold]Key Insights:[/bold]")
            for i, insight in enumerate(summary_data["key_insights"], 1):
                console.print(f"{i}. {insight}")
    
    def run_full_pipeline(self, limit: Optional[int] = None, date: Optional[datetime] = None) -> dict:
        """Run the complete processing pipeline."""
        console.print("[bold green]Starting Notion Processing Pipeline[/bold green]\n")
        
        try:
            # Step 1: Extract documents
            extracted_count = self.run_extraction_step(limit=limit)
            
            # Step 2: Classify documents
            classified_count = self.run_classification_step()
            
            # Step 3: Generate weekly summary
            summary_data = self.run_summary_step(date=date)
            
            # Display results
            console.print("\n[bold green]Pipeline completed successfully![/bold green]")
            console.print(f"Documents extracted: {extracted_count}")
            console.print(f"Documents classified: {classified_count}")
            
            # Display summary report
            self.display_summary_report(summary_data)
            
            return {
                "extracted_count": extracted_count,
                "classified_count": classified_count,
                "summary": summary_data
            }
        
        except Exception as e:
            console.print(f"\n[bold red]Pipeline failed: {str(e)}[/bold red]")
            logger.error("Pipeline execution failed", error=str(e))
            raise
    
    def run_extraction_only(self, limit: Optional[int] = None) -> int:
        """Run only the extraction step."""
        console.print("[bold blue]Running extraction only[/bold blue]")
        return self.run_extraction_step(limit=limit)
    
    def run_classification_only(self) -> int:
        """Run only the classification step."""
        console.print("[bold blue]Running classification only[/bold blue]")
        return self.run_classification_step()
    
    def run_summary_only(self, date: Optional[datetime] = None) -> dict:
        """Run only the summary step."""
        console.print("[bold blue]Running summary generation only[/bold blue]")
        return self.run_summary_step(date=date)
    
    def get_processing_stats(self) -> dict:
        """Get current processing statistics."""
        session = db_manager.get_session()
        
        try:
            # Count documents by status
            from .database import ProcessingRecordDB
            from .models import ProcessingStatus
            
            total_docs = session.query(ProcessingRecordDB).count()
            extracted_docs = session.query(ProcessingRecordDB).filter(
                ProcessingRecordDB.status == ProcessingStatus.EXTRACTED
            ).count()
            classified_docs = session.query(ProcessingRecordDB).filter(
                ProcessingRecordDB.status == ProcessingStatus.CLASSIFIED
            ).count()
            failed_docs = session.query(ProcessingRecordDB).filter(
                ProcessingRecordDB.status == ProcessingStatus.FAILED
            ).count()
            
            return {
                "total_documents": total_docs,
                "extracted": extracted_docs,
                "classified": classified_docs,
                "failed": failed_docs
            }
        
        except Exception as e:
            logger.error("Failed to get processing stats", error=str(e))
            raise
        finally:
            session.close()
    
    def display_processing_stats(self):
        """Display current processing statistics."""
        stats = self.get_processing_stats()
        
        console.print("\n[bold yellow]Processing Statistics[/bold yellow]")
        
        stats_table = Table()
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Count", style="green")
        
        stats_table.add_row("Total Documents", str(stats["total_documents"]))
        stats_table.add_row("Extracted", str(stats["extracted"]))
        stats_table.add_row("Classified", str(stats["classified"]))
        stats_table.add_row("Failed", str(stats["failed"]))
        
        console.print(stats_table)
    
    def cleanup(self):
        """Clean up resources."""
        try:
            db_manager.close()
            logger.info("Pipeline cleanup completed")
        except Exception as e:
            logger.error("Cleanup failed", error=str(e)) 