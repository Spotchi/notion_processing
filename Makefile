.PHONY: help install setup test clean format lint type-check run extract classify summarize stats config docker-up docker-down

help: ## Show this help message
	@echo "Notion Processing Pipeline - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	uv sync

install-dev: ## Install the package with development dependencies
	uv sync --extra dev

setup: ## Set up the database tables
	python -m notion_processing.cli setup

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ --cov=notion_processing --cov-report=html

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .venv/

format: ## Format code with black and isort
	uv run black notion_processing/ tests/
	uv run isort notion_processing/ tests/

lint: ## Run linting checks
	uv run flake8 notion_processing/ tests/
	uv run black --check notion_processing/ tests/
	uv run isort --check-only notion_processing/ tests/

type-check: ## Run type checking with mypy
	uv run mypy notion_processing/

quality: format lint type-check ## Run all code quality checks

run: ## Run the complete pipeline
	uv run python -m notion_processing.cli run

extract: ## Extract documents from Notion
	uv run python -m notion_processing.cli extract

classify: ## Classify extracted documents
	uv run python -m notion_processing.cli classify

summarize: ## Generate weekly summary
	uv run python -m notion_processing.cli summarize

stats: ## Show processing statistics
	uv run python -m notion_processing.cli stats

dashboard: ## Run Streamlit dashboard
	uv run python run_dashboard.py

dashboard-direct: ## Run Streamlit dashboard directly
	uv run streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0

sample-data: ## Generate sample weekly summary data for testing
	uv run python generate_sample_data.py

config: ## Show current configuration
	uv run python -m notion_processing.cli config

docker-up: ## Start local PostgreSQL and pgAdmin with Docker (for development)
	@echo "Note: This project now uses Supabase by default"
	@echo "To use local PostgreSQL for development, uncomment services in docker-compose.yml"
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-clean: ## Stop and remove Docker containers and volumes
	docker-compose down -v
	docker system prune -f

dev-setup: install-dev setup ## Complete development setup (uses Supabase)

# Example usage with environment variables
run-example: ## Run pipeline with example parameters
	NOTION_TOKEN=your_token \
	NOTION_DATABASE_ID=your_db_id \
	OPENAI_API_KEY=your_key \
	DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres \
	uv run python -m notion_processing.cli run --limit 5

# Database operations
db-migrate: ## Run database migrations (if using Alembic)
	uv run alembic upgrade head

db-rollback: ## Rollback database migrations
	uv run alembic downgrade -1

db-reset: setup ## Reset database completely (Supabase)

# Monitoring
logs: ## Show application logs
	tail -f logs/app.log

monitor: ## Monitor processing statistics
	watch -n 5 "uv run python -m notion_processing.cli stats"

# UV specific commands
uv-add: ## Add a new dependency
	uv add $(pkg)

uv-add-dev: ## Add a new development dependency
	uv add --dev $(pkg)

uv-remove: ## Remove a dependency
	uv remove $(pkg)

uv-update: ## Update all dependencies
	uv lock --upgrade

uv-sync: ## Sync dependencies 
	uv sync
