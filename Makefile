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
	@echo "Schema file: schemas/market_data.json"
	@echo "Generated dir: generated/"

build: ## Build the project (generate schema, validate syntax)
	python3 tools/schema_generator.py
	python3 -m py_compile services/data_ingestion/main.py
	python3 -m py_compile services/md_provider/main.py
	python3 -m py_compile services/health_check/main.py
	python3 -m py_compile tools/schema_generator.py

test: build ## Run all tests
	python3 -m pytest tests/ -v

check: build test ## Run full project validation (build + test + lint + typecheck)
	python3 -m black --check --diff services/ tools/ tests/
	python3 -m isort --check-only --diff services/ tools/ tests/
	python3 -m mypy services/ tools/ --ignore-missing-imports

clean: ## Clean generated files
	rm -rf generated/*
	mkdir -p generated

format: ## Format code with black
	python3 -m black services/ tools/ tests/

format-check: ## Check code formatting
	python3 -m black --check --diff services/ tools/ tests/

lint: ## Check code style and imports
	python3 -m isort --check-only --diff services/ tools/ tests/

lint-fix: ## Fix import order
	python3 -m isort services/ tools/ tests/

typecheck: ## Run type checking
	python3 -m mypy services/ tools/ --ignore-missing-imports

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

# Docker development workflows
docker-dev: docker-build docker-up ## Build and start Docker services

docker-restart: docker-down docker-up ## Restart Docker services