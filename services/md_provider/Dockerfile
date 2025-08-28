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
COPY services/md_provider/ ./services/md_provider/
COPY services/data_ingestion/database.py ./services/data_ingestion/database.py
COPY services/__init__.py ./services/
COPY services/data_ingestion/__init__.py ./services/data_ingestion/
COPY generated/ ./generated/

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=info

# Expose port
EXPOSE 8000

# Run the MD Provider service
CMD ["python3", "-m", "services.md_provider.main"]