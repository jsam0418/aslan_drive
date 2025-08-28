"""
Database connection and operations for data ingestion service
"""
import logging
import os
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager with connection URL."""
        self.database_url: str = (
            database_url
            or os.getenv(
                "DATABASE_URL",
                "postgresql://trader:trading123@localhost:5432/aslan_drive",
            )
            or "postgresql://trader:trading123@localhost:5432/aslan_drive"
        )

        self.engine = create_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
        )

        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def _is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return "sqlite" in str(self.engine.url).lower()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def execute_migration(self, migration_sql: str) -> bool:
        """Execute migration SQL script."""
        try:
            with self.engine.connect() as conn:
                # Split by statements and execute each
                statements = [
                    stmt.strip() for stmt in migration_sql.split(";") if stmt.strip()
                ]

                for stmt in statements:
                    if stmt:
                        conn.execute(text(stmt))
                        logger.debug(f"Executed: {stmt[:50]}...")

                conn.commit()
                logger.info("Migration executed successfully")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Migration failed: {e}")
            return False

    def insert_daily_ohlcv_data(self, data_records: list) -> int:
        """Insert daily OHLCV data records, return number of inserted records."""
        if not data_records:
            return 0

        inserted_count = 0

        try:
            with self.get_session() as session:  # type: Session
                for record in data_records:
                    # Convert Decimal to float for SQLite compatibility
                    converted_record = record.copy()
                    if self._is_sqlite():
                        from decimal import Decimal

                        for key, value in converted_record.items():
                            if isinstance(value, Decimal):
                                converted_record[key] = float(value)

                        # SQLite uses INSERT OR REPLACE
                        insert_sql = text(
                            """
                            INSERT OR REPLACE INTO daily_ohlcv 
                            (symbol, date, open, high, low, close, volume, created_at)
                            VALUES 
                            (:symbol, :date, :open, :high, :low, :close, :volume, :created_at)
                        """
                        )
                    else:
                        # PostgreSQL uses ON CONFLICT
                        insert_sql = text(
                            """
                            INSERT INTO daily_ohlcv 
                            (symbol, date, open, high, low, close, volume, created_at)
                            VALUES 
                            (:symbol, :date, :open, :high, :low, :close, :volume, :created_at)
                            ON CONFLICT (symbol, date) DO UPDATE SET
                                open = EXCLUDED.open,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                close = EXCLUDED.close,
                                volume = EXCLUDED.volume,
                                created_at = EXCLUDED.created_at
                        """
                        )

                    session.execute(insert_sql, converted_record)
                    inserted_count += 1

                logger.info(f"Inserted/updated {inserted_count} OHLCV records")

        except SQLAlchemyError as e:
            logger.error(f"Failed to insert OHLCV data: {e}")
            raise

        return inserted_count

    def insert_symbols_metadata(self, metadata_records: list) -> int:
        """Insert symbols metadata, return number of inserted records."""
        if not metadata_records:
            return 0

        inserted_count = 0

        try:
            with self.get_session() as session:  # type: Session
                for record in metadata_records:
                    if self._is_sqlite():
                        # SQLite uses INSERT OR REPLACE
                        insert_sql = text(
                            """
                            INSERT OR REPLACE INTO symbols 
                            (symbol, name, asset_class, exchange, currency, active, created_at, updated_at)
                            VALUES 
                            (:symbol, :name, :asset_class, :exchange, :currency, :active, :created_at, :updated_at)
                        """
                        )
                    else:
                        # PostgreSQL uses ON CONFLICT
                        insert_sql = text(
                            """
                            INSERT INTO symbols 
                            (symbol, name, asset_class, exchange, currency, active, created_at, updated_at)
                            VALUES 
                            (:symbol, :name, :asset_class, :exchange, :currency, :active, :created_at, :updated_at)
                            ON CONFLICT (symbol) DO UPDATE SET
                                name = EXCLUDED.name,
                                asset_class = EXCLUDED.asset_class,
                                exchange = EXCLUDED.exchange,
                                currency = EXCLUDED.currency,
                                active = EXCLUDED.active,
                                updated_at = EXCLUDED.updated_at
                        """
                        )

                    session.execute(insert_sql, record)
                    inserted_count += 1

                logger.info(
                    f"Inserted/updated {inserted_count} symbol metadata records"
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to insert symbols metadata: {e}")
            raise

        return inserted_count

    def get_latest_data_date(self, symbol: Optional[str] = None) -> Optional[str]:
        """Get the latest date for which we have data."""
        try:
            with self.get_session() as session:  # type: Session
                if symbol:
                    query = text(
                        "SELECT MAX(date) FROM daily_ohlcv WHERE symbol = :symbol"
                    )
                    result = session.execute(query, {"symbol": symbol}).scalar()
                else:
                    query = text("SELECT MAX(date) FROM daily_ohlcv")
                    result = session.execute(query).scalar()

                if result:
                    # Handle different database types
                    if hasattr(result, "isoformat"):
                        return result.isoformat()  # PostgreSQL returns date object
                    else:
                        return str(result)  # SQLite returns string
                return None

        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest data date: {e}")
            return None

    def check_data_exists_for_date(
        self, check_date: str, symbol: Optional[str] = None
    ) -> bool:
        """Check if data exists for a specific date."""
        try:
            with self.get_session() as session:  # type: Session
                if symbol:
                    query = text(
                        "SELECT COUNT(*) FROM daily_ohlcv WHERE date = :date AND symbol = :symbol"
                    )
                    count = session.execute(
                        query, {"date": check_date, "symbol": symbol}
                    ).scalar()
                else:
                    query = text("SELECT COUNT(*) FROM daily_ohlcv WHERE date = :date")
                    count = session.execute(query, {"date": check_date}).scalar()

                return bool(count and count > 0)

        except SQLAlchemyError as e:
            logger.error(f"Failed to check data existence: {e}")
            return False
