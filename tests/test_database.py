"""
Tests for the database manager
"""
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_database_connection(db_manager):
    """Test database connection."""
    assert db_manager.test_connection()


def test_insert_symbols_metadata(db_manager, sample_symbols_metadata):
    """Test inserting symbols metadata."""
    count = db_manager.insert_symbols_metadata(sample_symbols_metadata)
    assert count == len(sample_symbols_metadata)

    # Test that duplicate insert updates existing records
    count2 = db_manager.insert_symbols_metadata(sample_symbols_metadata)
    assert count2 == len(sample_symbols_metadata)  # Should update, not fail


def test_insert_ohlcv_data(db_manager, sample_ohlcv_data):
    """Test inserting OHLCV data."""
    count = db_manager.insert_daily_ohlcv_data(sample_ohlcv_data)
    assert count == len(sample_ohlcv_data)

    # Test that duplicate insert updates existing records
    count2 = db_manager.insert_daily_ohlcv_data(sample_ohlcv_data)
    assert count2 == len(sample_ohlcv_data)  # Should update, not fail


def test_get_latest_data_date(db_manager, sample_ohlcv_data):
    """Test getting latest data date."""
    # Insert sample data
    db_manager.insert_daily_ohlcv_data(sample_ohlcv_data)

    # Get latest date
    latest_date = db_manager.get_latest_data_date()
    assert latest_date is not None

    # Get latest date for specific symbol
    symbol = sample_ohlcv_data[0]["symbol"]
    latest_date_symbol = db_manager.get_latest_data_date(symbol)
    assert latest_date_symbol is not None


def test_check_data_exists_for_date(db_manager, sample_ohlcv_data):
    """Test checking if data exists for a specific date."""
    # Insert sample data
    db_manager.insert_daily_ohlcv_data(sample_ohlcv_data)

    # Check for existing date
    test_date = sample_ohlcv_data[0]["date"].isoformat()
    assert db_manager.check_data_exists_for_date(test_date)

    # Check for non-existing date
    future_date = (date.today() + timedelta(days=30)).isoformat()
    assert not db_manager.check_data_exists_for_date(future_date)

    # Check for specific symbol
    symbol = sample_ohlcv_data[0]["symbol"]
    assert db_manager.check_data_exists_for_date(test_date, symbol)


def test_empty_data_insertion(db_manager):
    """Test inserting empty data lists."""
    assert db_manager.insert_daily_ohlcv_data([]) == 0
    assert db_manager.insert_symbols_metadata([]) == 0
