# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aslan Drive is an algorithmic/quantitative trading infrastructure project with a Phase 0 skeleton implementation focused on OHLCV daily data processing, containerized services, and JSON schema-driven development.

## Project Architecture

### Core Components (Phase 0 Implementation)
1. **Data Ingestion Service** (`services/data_ingestion/`): Mock OHLCV data generator with PostgreSQL storage
2. **MD Provider API** (`services/md_provider/`): FastAPI REST service for market data queries
3. **Health Check Service** (`services/health_check/`): Database validation with Slack notifications
4. **Schema Generator** (`tools/schema_generator.py`): JSON→Python dataclasses + SQL migrations

### Technology Stack
- **Python 3.11+** with FastAPI, SQLAlchemy, pytest
- **PostgreSQL** with TimescaleDB-ready schemas
- **Docker + Docker Compose** for full containerization
- **Make** for build orchestration and development workflows
- **Slack API** for alerting and notifications

## Commands

### Essential Commands

#### Quick Start (Working Commands)
```bash
# Basic development (no dependencies needed)
make build              # Generate schema + validate syntax
python3 test_basic.py   # Run basic functionality tests

# Using development helper script
python3 dev.py build         # Build project
python3 dev.py test-basic    # Run basic tests
python3 dev.py schema-gen    # Generate schema files
```

#### Development Setup (with dependencies)
```bash
make dev-setup          # Create virtual environment + install deps
# OR manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Docker Operations (fully working)
```bash
make docker-build       # Build all Docker images
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-logs        # Follow service logs
```

#### Code Quality (requires dependencies)
```bash
make format             # Format code with black
make lint               # Check imports with isort
make typecheck          # Run mypy type checking
```

## JSON Schema-Driven Development

The project uses a unique schema-first approach:
- **Schema Definition**: `schemas/market_data.json` - Single source of truth
- **Code Generation**: `python3 tools/schema_generator.py` - Generates Python dataclasses, SQLAlchemy models, and SQL migrations
- **Automatic Updates**: When you modify the JSON schema, run `make schema-gen` to regenerate all dependent code

Example workflow for schema changes:
1. Edit `schemas/market_data.json`
2. Run `make schema-gen` 
3. Review generated files in `generated/`
4. Run `make test` to validate changes

## Development Environment

### Local Development
- Copy `.env.example` to `.env` and configure
- Run `make dev` for complete setup
- Use `make quick-test` for rapid development cycles

### Container Development  
- Run `make docker-dev` to build and start all services
- Access MD Provider API at `http://localhost:8000`
- PostgreSQL available at `localhost:5432`

### Testing
- Unit tests: `pytest tests/test_*.py`
- Integration tests: `pytest tests/test_integration.py`
- Database tests use SQLite for isolation

## Key Design Principles

- **Schema-First Development**: JSON schema drives all data structures
- **Containerized Services**: Full Docker Compose orchestration
- **Mock Data Foundation**: Realistic OHLCV data generation for testing
- **Health Check Integration**: Database validation with Slack notifications
- **Agile Infrastructure**: Always-working system ready for incremental features