# Database Migration Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/db_migration/ ./services/db_migration/
COPY services/__init__.py ./services/
COPY models/ ./models/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=info

# Run migration service
CMD ["python3", "-m", "services.db_migration.main"]