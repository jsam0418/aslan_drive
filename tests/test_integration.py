"""
Integration tests for the full system
"""
import pytest
import asyncio
from datetime import date, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.health_check.slack_notifier import SlackNotifier


def test_end_to_end_data_flow(db_manager, mock_generator):
    """Test complete data flow from generation to storage."""
    # Generate symbols metadata
    symbols_metadata = mock_generator.generate_symbols_metadata()
    
    # Insert symbols metadata
    count = db_manager.insert_symbols_metadata(symbols_metadata)
    assert count > 0
    
    # Generate OHLCV data
    test_date = date.today() - timedelta(days=1)
    ohlcv_data = mock_generator.generate_historical_data(
        symbols=["AAPL", "GOOGL"],
        start_date=test_date,
        end_date=test_date
    )
    
    # Insert OHLCV data
    count = db_manager.insert_daily_ohlcv_data(ohlcv_data)
    assert count > 0
    
    # Verify data exists
    assert db_manager.check_data_exists_for_date(test_date.isoformat())
    
    # Verify latest date
    latest_date = db_manager.get_latest_data_date()
    assert latest_date == test_date.isoformat()


@pytest.mark.asyncio
async def test_slack_notifier_without_webhook():
    """Test Slack notifier without actual webhook (logs only)."""
    notifier = SlackNotifier(webhook_url=None)
    
    # Should succeed but only log the message
    result = await notifier.send_notification("Test message")
    assert result is True
    
    # Test health check success notification
    result = await notifier.send_health_check_success(
        check_date="2024-01-15",
        records_found=100,
        symbols=["AAPL", "GOOGL"]
    )
    assert result is True
    
    # Test health check failure notification
    result = await notifier.send_health_check_failure(
        check_date="2024-01-15",
        error_message="Test error",
        database_connected=True
    )
    assert result is True


def test_weekend_data_handling(mock_generator):
    """Test that weekend data is properly excluded."""
    # Pick a date range that includes a weekend
    start_date = date(2024, 1, 6)  # Saturday
    end_date = date(2024, 1, 7)    # Sunday
    
    data = mock_generator.generate_historical_data(
        symbols=["AAPL"],
        start_date=start_date,
        end_date=end_date
    )
    
    # Should be empty since weekends are excluded
    assert len(data) == 0
    
    # Test with weekday
    weekday_data = mock_generator.generate_historical_data(
        symbols=["AAPL"],
        start_date=date(2024, 1, 8),  # Monday
        end_date=date(2024, 1, 8)
    )
    
    assert len(weekday_data) == 1


def test_large_data_set_handling(db_manager, mock_generator):
    """Test handling of larger data sets."""
    # Generate 30 days of data for 5 symbols
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    data = mock_generator.generate_historical_data(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )
    
    # Should have roughly 22 weekdays * 5 symbols (accounting for weekends)
    assert len(data) > 100  # Conservative estimate
    
    # Insert in batches to simulate real usage
    batch_size = 50
    total_inserted = 0
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        count = db_manager.insert_daily_ohlcv_data(batch)
        total_inserted += count
    
    assert total_inserted == len(data)