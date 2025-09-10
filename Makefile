# X-Tracker Makefile
# Convenient commands for development and deployment

.PHONY: help install init ui status test clean backup

help: ## Show this help message
	@echo "🚀 X-Tracker Command Center"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv
	uv sync
	@echo "✅ Dependencies installed"

init: ## Initialize X-Tracker (database, directories)
	uv run python main.py init

ui: ## Launch the web UI
	uv run python main.py ui

status: ## Show system status
	uv run python main.py status

test: ## Test API credentials and connectivity
	uv run python main.py test

# Legacy script compatibility
track-competitors: ## Track competitors (legacy)
	uv run python scripts/archive/competitor_tracker.py

clean-inactive: ## Run inactive account cleaner (legacy)
	uv run python scripts/archive/inactive_account_cleaner.py --dry-run

growth-center: ## Run growth center (legacy)
	uv run python scripts/archive/x_growth_center.py

# Development commands
dev-ui: ## Launch UI in development mode with auto-reload
	uv run python main.py ui --debug

share-ui: ## Launch UI with public sharing enabled
	uv run python main.py ui --share

# Database commands
backup: ## Backup database
	@echo "Creating database backup..."
	@mkdir -p data/backups
	@cp data/x_tracker.db "data/backups/x_tracker_backup_$(shell date +%Y%m%d_%H%M%S).db" 2>/dev/null || true
	@echo "✅ Database backed up"

clean: ## Clean temporary files and logs
	rm -rf logs/*.log
	rm -rf reports/daily/*
	rm -rf __pycache__ src/**/__pycache__
	@echo "✅ Cleaned temporary files"

# Setup commands
setup-env: ## Copy .env.example to .env if it doesn't exist
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please edit .env and add your API credentials"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

# Docker commands (future)
docker-build: ## Build Docker image
	docker build -t x-tracker .

docker-run: ## Run with Docker
	docker-compose up -d

# Default target
.DEFAULT_GOAL := ui