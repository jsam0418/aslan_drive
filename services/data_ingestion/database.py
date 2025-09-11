"""
Database connection and operations for data ingestion service
"""
import logging
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path for models import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import DailyOHLCV, Symbol

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

    def insert_daily_ohlcv_data(self, data_records: List[dict]) -> int:
        """Insert daily OHLCV data records using SQLAlchemy ORM."""
        if not data_records:
            return 0

        inserted_count = 0

        try:
            with self.get_session() as session:
                for record in data_records:
                    # Create DailyOHLCV instance
                    ohlcv_record = DailyOHLCV(**record)

                    if self._is_sqlite():
                        # For SQLite, use merge (upsert)
                        session.merge(ohlcv_record)
                    else:
                        # For PostgreSQL, use upsert with ON CONFLICT
                        stmt = pg_insert(DailyOHLCV).values(**record)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["symbol", "date"],
                            set_={
                                "open": stmt.excluded.open,
                                "high": stmt.excluded.high,
                                "low": stmt.excluded.low,
                                "close": stmt.excluded.close,
                                "volume": stmt.excluded.volume,
                                "created_at": stmt.excluded.created_at,
                            },
                        )
                        session.execute(stmt)

                    inserted_count += 1

                logger.info(f"Inserted/updated {inserted_count} OHLCV records")

        except SQLAlchemyError as e:
            logger.error(f"Failed to insert OHLCV data: {e}")
            raise

        return inserted_count

    def insert_symbols_metadata(self, metadata_records: List[dict]) -> int:
        """Insert symbols metadata using SQLAlchemy ORM."""
        if not metadata_records:
            return 0

        inserted_count = 0

        try:
            with self.get_session() as session:
                for record in metadata_records:
                    # Create Symbol instance
                    symbol_record = Symbol(**record)

                    if self._is_sqlite():
                        # For SQLite, use merge (upsert)
                        session.merge(symbol_record)
                    else:
                        # For PostgreSQL, use upsert with ON CONFLICT
                        stmt = pg_insert(Symbol).values(**record)
                        stmt = stmt.on_conflict_do_update(
                            index_elements=["symbol"],
                            set_={
                                "name": stmt.excluded.name,
                                "asset_class": stmt.excluded.asset_class,
                                "exchange": stmt.excluded.exchange,
                                "currency": stmt.excluded.currency,
                                "active": stmt.excluded.active,
                                "updated_at": stmt.excluded.updated_at,
                            },
                        )
                        session.execute(stmt)

                    inserted_count += 1

                logger.info(
                    f"Inserted/updated {inserted_count} symbol metadata records"
                )

        except SQLAlchemyError as e:
            logger.error(f"Failed to insert symbols metadata: {e}")
            raise

        return inserted_count

    def get_latest_data_date(self, symbol: Optional[str] = None) -> Optional[str]:
        """Get the latest date for which we have data using SQLAlchemy ORM."""
        try:
            with self.get_session() as session:
                from sqlalchemy import func

                query = session.query(func.max(DailyOHLCV.date))

                if symbol:
                    query = query.filter(DailyOHLCV.symbol == symbol)

                result = query.scalar()

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
        """Check if data exists for a specific date using SQLAlchemy ORM."""
        try:
            with self.get_session() as session:
                from sqlalchemy import func

                query = session.query(func.count(DailyOHLCV.symbol))
                query = query.filter(DailyOHLCV.date == check_date)

                if symbol:
                    query = query.filter(DailyOHLCV.symbol == symbol)

                count = query.scalar()
                return bool(count and count > 0)

        except SQLAlchemyError as e:
            logger.error(f"Failed to check data existence: {e}")
            return False
