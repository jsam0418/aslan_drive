"""
Data Ingestion Service - Main Entry Point

Generates mock OHLCV data and loads it into the database.
"""
import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pytz

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.database import DatabaseManager
from services.data_ingestion.mock_data_generator import MockOHLCVGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_target_trade_date() -> date:
    """
    Determine the correct trade date based on current time and market hours.

    Market closes at 4:00 PM Central Time (5:00 PM ET).
    - If before 4:00 PM CT and it's a weekday, load previous trading day
    - If after 4:00 PM CT and it's a weekday, load current day
    - If weekend, load Friday's data
    """
    # Get current time in Central Time
    central_tz = pytz.timezone("US/Central")
    now_ct = datetime.now(central_tz)
    current_date = now_ct.date()

    logger.info(f"Current time (Central): {now_ct}")

    # If it's weekend, return Friday
    if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        days_back = current_date.weekday() - 4  # Go back to Friday
        target_date = current_date - timedelta(days=days_back)
        logger.info(f"Weekend detected, targeting Friday: {target_date}")
        return target_date

    # If it's a weekday, check if market has closed (4:00 PM CT)
    market_close_hour = 16  # 4:00 PM

    if now_ct.hour >= market_close_hour:
        # Market has closed, use today's date
        target_date = current_date
        logger.info(
            f"After market close ({market_close_hour}:00 CT), targeting today: {target_date}"
        )
    else:
        # Market hasn't closed yet, use previous trading day
        if current_date.weekday() == 0:  # Monday
            target_date = current_date - timedelta(days=3)  # Friday
        else:
            target_date = current_date - timedelta(days=1)  # Previous day
        logger.info(
            f"Before market close ({market_close_hour}:00 CT), targeting previous day: {target_date}"
        )

    return target_date


def ensure_tables_exist(db_manager: DatabaseManager) -> bool:
    """Ensure database tables exist using SQLAlchemy models."""
    try:
        from models.base import Base

        # Create all tables if they don't exist
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Database tables created/verified successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


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

    # Ensure tables exist (idempotent)
    logger.info("Ensuring database tables exist...")
    if not ensure_tables_exist(db_manager):
        logger.error("Database table creation failed. Exiting.")
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
    # Use the correct trade date based on market hours
    end_date = get_target_trade_date()
    start_date = end_date - timedelta(days=365)

    logger.info(f"Generating historical data from {start_date} to {end_date}")

    # Generate OHLCV data
    ohlcv_data = generator.generate_historical_data(
        start_date=start_date, end_date=end_date
    )

    # Insert data in batches
    batch_size = 1000
    total_batches = len(ohlcv_data) // batch_size + (
        1 if len(ohlcv_data) % batch_size else 0
    )

    logger.info(f"Inserting {len(ohlcv_data)} records in {total_batches} batches")

    for i in range(0, len(ohlcv_data), batch_size):
        batch = ohlcv_data[i : i + batch_size]
        batch_num = (i // batch_size) + 1

        logger.info(f"Processing batch {batch_num}/{total_batches}")
        db_manager.insert_daily_ohlcv_data(batch)

    logger.info("One-time data ingestion completed successfully")


def run_continuous_ingestion(
    db_manager: DatabaseManager, generator: MockOHLCVGenerator
):
    """Run continuous data ingestion (generates today's data periodically)."""
    sleep_interval = int(
        os.getenv("INGESTION_INTERVAL_SECONDS", "3600")
    )  # Default 1 hour

    logger.info(f"Starting continuous ingestion with {sleep_interval}s interval")

    while True:
        try:
            # Get the correct trade date
            target_date = get_target_trade_date()

            # Check if we already have data for the target date
            if db_manager.check_data_exists_for_date(target_date.isoformat()):
                logger.info(
                    f"Data for {target_date} already exists, skipping generation"
                )
            else:
                logger.info(f"Generating data for {target_date}")

                # Generate data for the target date
                target_data = generator.generate_historical_data(
                    start_date=target_date, end_date=target_date
                )

                if target_data:
                    db_manager.insert_daily_ohlcv_data(target_data)
                    logger.info(
                        f"Inserted {len(target_data)} records for {target_date}"
                    )
                else:
                    logger.info(f"No data generated for {target_date} (weekend?)")

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
