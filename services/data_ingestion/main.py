"""
Data Ingestion Service - Main Entry Point

Generates mock OHLCV data and loads it into the database.
"""
import os
import sys
import time
import logging
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.mock_data_generator import MockOHLCVGenerator
from services.data_ingestion.database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_migration_sql() -> str:
    """Load the migration SQL from generated files."""
    migration_file = project_root / "generated" / "migration.sql"
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    with open(migration_file, 'r') as f:
        return f.read()


def main():
    """Main data ingestion process."""
    logger.info("Starting Data Ingestion Service...")
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Test database connection
    logger.info("Testing database connection...")
    if not db_manager.test_connection():
        logger.error("Database connection failed. Exiting.")
        sys.exit(1)
    
    # Run migration (idempotent)
    logger.info("Running database migration...")
    migration_sql = load_migration_sql()
    if not db_manager.execute_migration(migration_sql):
        logger.error("Database migration failed. Exiting.")
        sys.exit(1)
    
    # Initialize mock data generator
    generator = MockOHLCVGenerator()
    
    # Insert symbols metadata first
    logger.info("Inserting symbols metadata...")
    symbols_metadata = generator.generate_symbols_metadata()
    db_manager.insert_symbols_metadata(symbols_metadata)
    
    # Check if we should run in continuous mode or one-time mode
    continuous_mode = os.getenv("CONTINUOUS_MODE", "false").lower() == "true"
    
    if continuous_mode:
        logger.info("Running in continuous mode...")
        run_continuous_ingestion(db_manager, generator)
    else:
        logger.info("Running in one-time mode...")
        run_onetime_ingestion(db_manager, generator)


def run_onetime_ingestion(db_manager: DatabaseManager, generator: MockOHLCVGenerator):
    """Run a one-time data ingestion for historical data."""
    # Generate data for the last year up to yesterday
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    
    logger.info(f"Generating historical data from {start_date} to {end_date}")
    
    # Generate OHLCV data
    ohlcv_data = generator.generate_historical_data(
        start_date=start_date,
        end_date=end_date
    )
    
    # Insert data in batches
    batch_size = 1000
    total_batches = len(ohlcv_data) // batch_size + (1 if len(ohlcv_data) % batch_size else 0)
    
    logger.info(f"Inserting {len(ohlcv_data)} records in {total_batches} batches")
    
    for i in range(0, len(ohlcv_data), batch_size):
        batch = ohlcv_data[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches}")
        db_manager.insert_daily_ohlcv_data(batch)
    
    logger.info("One-time data ingestion completed successfully")


def run_continuous_ingestion(db_manager: DatabaseManager, generator: MockOHLCVGenerator):
    """Run continuous data ingestion (generates today's data periodically)."""
    sleep_interval = int(os.getenv("INGESTION_INTERVAL_SECONDS", "3600"))  # Default 1 hour
    
    logger.info(f"Starting continuous ingestion with {sleep_interval}s interval")
    
    while True:
        try:
            # Generate today's data
            today = date.today()
            
            # Check if we already have today's data
            if db_manager.check_data_exists_for_date(today.isoformat()):
                logger.info(f"Data for {today} already exists, skipping generation")
            else:
                logger.info(f"Generating data for {today}")
                
                # Generate data for today
                todays_data = generator.generate_historical_data(
                    start_date=today,
                    end_date=today
                )
                
                if todays_data:
                    db_manager.insert_daily_ohlcv_data(todays_data)
                    logger.info(f"Inserted {len(todays_data)} records for {today}")
                else:
                    logger.info(f"No data generated for {today} (weekend?)")
            
            logger.info(f"Sleeping for {sleep_interval} seconds...")
            time.sleep(sleep_interval)
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in continuous ingestion: {e}")
            logger.info(f"Sleeping for {sleep_interval} seconds before retry...")
            time.sleep(sleep_interval)


if __name__ == "__main__":
    main()