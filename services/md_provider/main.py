"""
Market Data Provider Service - Main Entry Point

FastAPI server for the MD Provider API.
"""
import os
import logging
import uvicorn
from services.md_provider.api import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Start the FastAPI server."""
    host = os.getenv("MD_PROVIDER_HOST", "0.0.0.0")
    port = int(os.getenv("MD_PROVIDER_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting MD Provider API server on {host}:{port}")
    
    uvicorn.run(
        "services.md_provider.api:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False  # Set to True for development
    )


if __name__ == "__main__":
    main()