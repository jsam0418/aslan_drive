"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import tempfile
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

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
    
    # Load and execute migration
    migration_file = project_root / "generated" / "migration.sql"
    if migration_file.exists():
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
            # Convert PostgreSQL SQL to SQLite compatible
            sqlite_migration = migration_sql.replace(
                "CREATE TABLE IF NOT EXISTS", "CREATE TABLE"
            ).replace(
                "DECIMAL(15,4)", "REAL"
            ).replace(
                "BIGINT", "INTEGER"
            ).replace(
                "TIMESTAMP WITH TIME ZONE", "DATETIME"
            ).replace(
                "CURRENT_TIMESTAMP", "datetime('now')"
            ).replace(
                "VARCHAR(20)", "TEXT"
            ).replace(
                "VARCHAR(255)", "TEXT"
            ).replace(
                "VARCHAR(50)", "TEXT"
            ).replace(
                "VARCHAR(3)", "TEXT"
            ).replace(
                "BOOLEAN", "INTEGER"
            )
            
            try:
                manager.execute_migration(sqlite_migration)
            except Exception as e:
                print(f"Migration warning: {e}")
    
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
        end_date=date.today() - timedelta(days=1)
    )


@pytest.fixture
def sample_symbols_metadata(mock_generator):
    """Generate sample symbols metadata for testing."""
    return mock_generator.generate_symbols_metadata()[:2]  # Just first 2 symbols