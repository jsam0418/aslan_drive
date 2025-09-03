"""
Health Check Service - Main Entry Point

Checks database for today's data and sends Slack notification with results.
"""
import asyncio
import logging
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.database import DatabaseManager
from services.health_check.slack_notifier import SlackNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def perform_health_check():
    """Perform comprehensive health check of the system."""
    logger.info("Starting health check...")

    # Initialize components
    db_manager = DatabaseManager()
    slack_notifier = SlackNotifier()

    check_date = date.today()

    # If it's weekend, check for Friday's data instead
    if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
        days_back = check_date.weekday() - 4  # Go back to Friday
        check_date = check_date - timedelta(days=days_back)
        logger.info(f"Weekend detected, checking for {check_date} data instead")

    try:
        # Test database connection
        logger.info("Testing database connection...")
        db_connected = db_manager.test_connection()

        if not db_connected:
            await slack_notifier.send_health_check_failure(
                check_date=check_date.isoformat(),
                error_message="Database connection failed",
                database_connected=False,
            )
            return False

        logger.info("Database connection successful")

        # Check if data exists for the target date
        logger.info(f"Checking for data on {check_date}")
        data_exists = db_manager.check_data_exists_for_date(check_date.isoformat())

        # If no data for today and it's early in the day, check yesterday's data
        if not data_exists and datetime.now().hour < 12:
            yesterday = check_date - timedelta(days=1)
            # Skip weekend days for yesterday check too
            if yesterday.weekday() >= 5:
                yesterday = yesterday - timedelta(days=(yesterday.weekday() - 4))
            logger.info(
                f"No data for {check_date}, checking {yesterday} instead (early day fallback)"
            )
            data_exists = db_manager.check_data_exists_for_date(yesterday.isoformat())
            if data_exists:
                check_date = yesterday

        if not data_exists:
            await slack_notifier.send_health_check_failure(
                check_date=check_date.isoformat(),
                error_message=f"No data found for {check_date}. Data ingestion may have failed.",
                database_connected=True,
            )
            return False

        # Get detailed information about the data
        with db_manager.get_session() as session:
            from sqlalchemy import text

            # Count records for the date
            record_count_result = session.execute(
                text("SELECT COUNT(*) FROM daily_ohlcv WHERE date = :date"),
                {"date": check_date},
            )
            record_count = record_count_result.scalar() or 0

            # Get symbols for the date
            symbols_result = session.execute(
                text(
                    "SELECT DISTINCT symbol FROM daily_ohlcv WHERE date = :date ORDER BY symbol"
                ),
                {"date": check_date},
            )
            symbols = [row[0] for row in symbols_result.fetchall()]

            # Get overall database statistics
            total_records_result = session.execute(
                text("SELECT COUNT(*) FROM daily_ohlcv")
            )
            total_records = total_records_result.scalar()

            total_symbols_result = session.execute(
                text("SELECT COUNT(*) FROM symbols WHERE active = true")
            )
            total_symbols = total_symbols_result.scalar()

            latest_date_result = session.execute(
                text("SELECT MAX(date) FROM daily_ohlcv")
            )
            latest_date = latest_date_result.scalar()

        database_stats = {
            "total_records": total_records,
            "total_symbols": total_symbols,
            "latest_date": latest_date.isoformat() if latest_date else None,
        }

        logger.info(
            f"Health check passed: Found {record_count} records for {len(symbols)} symbols on {check_date}"
        )

        # Send success notification
        await slack_notifier.send_health_check_success(
            check_date=check_date.isoformat(),
            records_found=record_count,
            symbols=symbols,
            database_stats=database_stats,
        )

        return True

    except Exception as e:
        logger.error(f"Health check failed with error: {e}")

        await slack_notifier.send_health_check_failure(
            check_date=check_date.isoformat(),
            error_message=f"Health check exception: {str(e)}",
            database_connected=db_connected,
        )

        return False


async def run_continuous_health_check():
    """Run health check in continuous mode."""
    interval = int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "3600"))  # Default 1 hour

    logger.info(f"Starting continuous health check with {interval}s interval")

    while True:
        try:
            success = await perform_health_check()

            if success:
                logger.info("Health check passed")
            else:
                logger.warning("Health check failed")

            logger.info(f"Sleeping for {interval} seconds...")
            await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in continuous health check: {e}")
            await asyncio.sleep(interval)


def main():
    """Main entry point for health check service."""
    logger.info("Starting Health Check Service...")

    # Check if running in continuous mode
    continuous_mode = os.getenv("CONTINUOUS_MODE", "false").lower() == "true"

    try:
        if continuous_mode:
            asyncio.run(run_continuous_health_check())
        else:
            # Single run mode
            success = asyncio.run(perform_health_check())

            if success:
                logger.info("Health check completed successfully")
                sys.exit(0)
            else:
                logger.error("Health check failed")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Health check service interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Health check service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
