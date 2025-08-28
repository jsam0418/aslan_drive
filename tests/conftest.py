"""
Pytest configuration and shared fixtures
"""
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.database import DatabaseManager
from services.data_ingestion.mock_data_generator import MockOHLCVGenerator


@pytest.fixture(scope="session")
def test_database_url():
    """Create a test database URL."""
    return "sqlite:///test_aslan_drive.db"


@pytest.fixture
def db_manager(test_database_url):
    """Create a test database manager."""
    manager = DatabaseManager(test_database_url)

    # Create test tables directly for SQLite
    try:
        with manager.engine.connect() as conn:
            # Create daily_ohlcv table
            conn.execute(
                text(
                    """
                CREATE TABLE daily_ohlcv (
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            """
                )
            )

            # Create symbols table
            conn.execute(
                text(
                    """
                CREATE TABLE symbols (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    asset_class TEXT NOT NULL,
                    exchange TEXT,
                    currency TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )

            conn.commit()
    except Exception as e:
        print(f"Table creation warning: {e}")

    yield manager

    # Cleanup
    try:
        os.unlink("test_aslan_drive.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_generator():
    """Create a mock data generator."""
    return MockOHLCVGenerator(seed=42)  # Fixed seed for reproducible tests


@pytest.fixture
def sample_ohlcv_data(mock_generator):
    """Generate sample OHLCV data for testing."""
    return mock_generator.generate_historical_data(
        symbols=["AAPL", "GOOGL"],
        start_date=date.today() - timedelta(days=7),
        end_date=date.today() - timedelta(days=1),
    )


@pytest.fixture
def sample_symbols_metadata(mock_generator):
    """Generate sample symbols metadata for testing."""
    return mock_generator.generate_symbols_metadata()[:2]  # Just first 2 symbols
