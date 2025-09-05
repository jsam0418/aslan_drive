FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/data_ingestion/ ./services/data_ingestion/
COPY services/__init__.py ./services/
COPY models/ ./models/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=info

# Run the data ingestion service
CMD ["python3", "-m", "services.data_ingestion.main"]