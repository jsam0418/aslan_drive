"""
Market Data Provider API

FastAPI-based REST API for serving OHLCV data from the database.
"""
import os
import sys
from contextlib import asynccontextmanager
from datetime import date as Date, datetime as DateTime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.database import DatabaseManager


# Pydantic models for API responses
class OHLCVData(BaseModel):
    symbol: str = Field(..., description="Financial instrument symbol")
    date: Date = Field(..., description="Trading date")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price")
    low: float = Field(..., description="Lowest price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(..., description="Trading volume")
    created_at: DateTime = Field(..., description="Record creation timestamp")

    class Config:
        json_encoders = {
            Date: lambda v: v.isoformat(),
            DateTime: lambda v: v.isoformat(),
        }


class SymbolMetadata(BaseModel):
    symbol: str = Field(..., description="Financial instrument symbol")
    name: Optional[str] = Field(None, description="Full name of the instrument")
    asset_class: str = Field(..., description="Asset class")
    exchange: Optional[str] = Field(None, description="Primary exchange")
    currency: str = Field(..., description="Base currency")
    active: bool = Field(..., description="Whether symbol is actively tracked")
    created_at: DateTime = Field(..., description="Record creation timestamp")
    updated_at: DateTime = Field(..., description="Record last updated timestamp")

    class Config:
        json_encoders = {DateTime: lambda v: v.isoformat()}


class HealthStatus(BaseModel):
    status: str = Field(..., description="Service health status")
    database_connected: bool = Field(..., description="Database connectivity status")
    latest_data_date: Optional[str] = Field(
        None, description="Latest available data date"
    )
    total_symbols: Optional[int] = Field(None, description="Total number of symbols")
    total_records: Optional[int] = Field(None, description="Total OHLCV records")


# Global database manager
db_manager = None


def get_db_manager() -> DatabaseManager:
    """Dependency to get database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup services."""
    global db_manager
    db_manager = DatabaseManager()

    # Test database connection
    if not db_manager.test_connection():
        raise RuntimeError("Failed to connect to database")

    yield

    # Cleanup on shutdown
    db_manager = None


# Initialize FastAPI app
app = FastAPI(
    title="Aslan Drive Market Data Provider",
    description="REST API for accessing historical OHLCV market data",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthStatus)
async def health_check(db: DatabaseManager = Depends(get_db_manager)):
    """Health check endpoint with database status."""
    try:
        # Test database connection
        db_connected = db.test_connection()

        if not db_connected:
            return HealthStatus(
                status="unhealthy",
                database_connected=False,
                latest_data_date=None,
                total_symbols=None,
                total_records=None,
            )

        # Get database statistics
        with db.get_session() as session:  # type: Session
            # Get latest data date
            latest_date_result = session.execute(
                text("SELECT MAX(date) FROM daily_ohlcv")
            ).scalar()
            latest_date = latest_date_result.isoformat() if latest_date_result else None

            # Get total symbols
            total_symbols = session.execute(
                text("SELECT COUNT(*) FROM symbols")
            ).scalar()

            # Get total records
            total_records = session.execute(
                text("SELECT COUNT(*) FROM daily_ohlcv")
            ).scalar()

        return HealthStatus(
            status="healthy",
            database_connected=True,
            latest_data_date=latest_date,
            total_symbols=total_symbols,
            total_records=total_records,
        )

    except Exception as e:
        return HealthStatus(
            status="unhealthy",
            database_connected=False,
            latest_data_date=None,
            total_symbols=None,
            total_records=None,
        )


@app.get("/symbols", response_model=List[SymbolMetadata])
async def get_symbols(
    active_only: bool = Query(True, description="Return only active symbols"),
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """Get list of available symbols with metadata."""
    try:
        with db.get_session() as session:  # type: Session
            query = "SELECT * FROM symbols"
            conditions = []
            params: Dict[str, Any] = {}

            if active_only:
                conditions.append("active = :active")
                params["active"] = True

            if asset_class:
                conditions.append("asset_class = :asset_class")
                params["asset_class"] = asset_class

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY symbol"

            result = session.execute(text(query), params)
            rows = result.fetchall()

            return [
                SymbolMetadata(
                    symbol=row[0],
                    name=row[1],
                    asset_class=row[2],
                    exchange=row[3],
                    currency=row[4],
                    active=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                )
                for row in rows
            ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/ohlcv/{symbol}", response_model=List[OHLCVData])
async def get_ohlcv_data(
    symbol: str,
    start_date: Optional[Date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[Date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of records"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """Get OHLCV data for a specific symbol."""
    try:
        with db.get_session() as session:  # type: Session
            query = """
                SELECT symbol, date, open, high, low, close, volume, created_at 
                FROM daily_ohlcv 
                WHERE symbol = :symbol
            """
            params: Dict[str, Any] = {"symbol": symbol.upper()}

            if start_date:
                query += " AND date >= :start_date"
                params["start_date"] = start_date

            if end_date:
                query += " AND date <= :end_date"
                params["end_date"] = end_date

            query += " ORDER BY date DESC LIMIT :limit"
            params["limit"] = limit

            result = session.execute(text(query), params)
            rows = result.fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404, detail=f"No data found for symbol {symbol}"
                )

            return [
                OHLCVData(
                    symbol=row[0],
                    date=row[1],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=row[6],
                    created_at=row[7],
                )
                for row in rows
            ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/ohlcv", response_model=List[OHLCVData])
async def get_multi_symbol_ohlcv(
    symbols: str = Query(..., description="Comma-separated list of symbols"),
    date_filter: Optional[Date] = Query(None, description="Specific date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of records"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """Get OHLCV data for multiple symbols."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]

        if len(symbol_list) > 50:  # Limit to prevent abuse
            raise HTTPException(
                status_code=400, detail="Too many symbols requested (max 50)"
            )

        with db.get_session() as session:  # type: Session
            placeholders = ",".join([f":symbol_{i}" for i in range(len(symbol_list))])
            query = f"""
                SELECT symbol, date, open, high, low, close, volume, created_at 
                FROM daily_ohlcv 
                WHERE symbol IN ({placeholders})
            """

            params: Dict[str, Any] = {
                f"symbol_{i}": symbol for i, symbol in enumerate(symbol_list)
            }

            if date_filter:
                query += " AND date = :date_filter"
                params["date_filter"] = date_filter

            query += " ORDER BY symbol, date DESC LIMIT :limit"
            params["limit"] = limit

            result = session.execute(text(query), params)
            rows = result.fetchall()

            return [
                OHLCVData(
                    symbol=row[0],
                    date=row[1],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=row[6],
                    created_at=row[7],
                )
                for row in rows
            ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/latest", response_model=List[OHLCVData])
async def get_latest_data(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    db: DatabaseManager = Depends(get_db_manager),
):
    """Get the most recent data for specified symbols or all symbols."""
    try:
        with db.get_session() as session:  # type: Session
            params: Dict[str, Any] = {}
            if symbols:
                symbol_list = [s.strip().upper() for s in symbols.split(",")]
                placeholders = ",".join(
                    [f":symbol_{i}" for i in range(len(symbol_list))]
                )
                params = {f"symbol_{i}": symbol for i, symbol in enumerate(symbol_list)}

                query = f"""
                    SELECT DISTINCT ON (symbol) symbol, date, open, high, low, close, volume, created_at
                    FROM daily_ohlcv 
                    WHERE symbol IN ({placeholders})
                    ORDER BY symbol, date DESC
                """
            else:
                query = """
                    SELECT DISTINCT ON (symbol) symbol, date, open, high, low, close, volume, created_at
                    FROM daily_ohlcv 
                    ORDER BY symbol, date DESC
                """
                params = {}

            result = session.execute(text(query), params)
            rows = result.fetchall()

            return [
                OHLCVData(
                    symbol=row[0],
                    date=row[1],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=row[6],
                    created_at=row[7],
                )
                for row in rows
            ]

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
