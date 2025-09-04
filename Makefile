# Aslan Drive Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help build test clean docker-build docker-up docker-down dev-setup info

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Aslan Drive Trading Infrastructure"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

info: ## Show project information
	@echo "Aslan Drive Trading Infrastructure v0.1.0"
	@echo "Python: $(shell which python3)"
	@echo "Models directory: models/"
	@echo "Alembic migrations: alembic/versions/"

build: ## Build the project (validate syntax)
	python3 -m py_compile models/base.py
	python3 -m py_compile models/market_data.py
	python3 -m py_compile services/data_ingestion/main.py
	python3 -m py_compile services/md_provider/main.py
	python3 -m py_compile services/health_check/main.py
	python3 -m py_compile services/db_migration/main.py

test: build ## Run all tests
	python3 -m pytest tests/ -v

check: build test ## Run full project validation (build + test + lint + typecheck)
	python3 -m black --check --diff services/ tools/ tests/
	python3 -m isort --check-only --diff services/ tools/ tests/
	python3 -m mypy services/ tools/ --ignore-missing-imports

clean: ## Clean generated files
	rm -rf generated/*
	mkdir -p generated

format: ## Format code with black and isort
	@which python3 > /dev/null || (echo "Python 3 not found" && exit 1)
	python3 -m isort services/ models/ tests/ || (echo "Run: pip install isort" && exit 1)
	python3 -m black services/ models/ tests/ || (echo "Run: pip install black" && exit 1)

format-check: ## Check code formatting
	@which python3 > /dev/null || (echo "Python 3 not found" && exit 1)
	python3 -m black --check --diff services/ models/ tests/ || (echo "Run: pip install black" && exit 1)

lint: ## Check code style and imports
	@which python3 > /dev/null || (echo "Python 3 not found" && exit 1)
	python3 -m isort --check-only --diff services/ models/ tests/ || (echo "Run: pip install isort" && exit 1)

lint-fix: ## Fix import order
	@which python3 > /dev/null || (echo "Python 3 not found" && exit 1)
	python3 -m isort services/ models/ tests/ || (echo "Run: pip install isort" && exit 1)

typecheck: ## Run type checking
	@if [ -d "venv" ]; then \
		./venv/bin/python -m mypy services/ models/ --ignore-missing-imports || (echo "Run: pip install mypy" && exit 1); \
	else \
		which python3 > /dev/null || (echo "Python 3 not found" && exit 1); \
		python3 -m mypy services/ models/ --ignore-missing-imports || (echo "Run: pip install mypy" && exit 1); \
	fi

docker-build: build ## Build Docker images
	docker-compose build

docker-up: docker-build ## Start all Docker services
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## Follow Docker service logs
	docker-compose logs -f

db-reset: ## Reset database with fresh schema
	docker-compose down -v
	docker-compose up -d postgres
	sleep 10
	python3 tools/schema_generator.py

dev-setup: ## Set up development environment
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

schema-gen: ## Generate schema files
	python3 tools/schema_generator.py

# Quick development workflows
dev: dev-setup schema-gen ## Set up development environment and generate schema

quick-test: build test ## Quick build and test

full-check: clean build test lint typecheck ## Full validation pipeline

ci-local: ## Run local CI/CD pipeline simulation
	@echo "🚀 Running Local CI/CD Pipeline..."
	@echo "================================="
	@$(MAKE) build
	@$(MAKE) format-check
	@$(MAKE) lint  
	@$(MAKE) typecheck
	@echo "✅ All CI/CD checks passed locally!"
	@echo "You can safely push your changes."

# Docker development workflows
docker-dev: docker-build docker-up ## Build and start Docker services

docker-restart: docker-down docker-up ## Restart Docker services