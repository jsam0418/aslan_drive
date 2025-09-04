"""
Market Data Models for Aslan Drive
"""
from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Numeric, String
from sqlalchemy.sql import func

from .base import Base, TimestampMixin


class DailyOHLCV(Base):
    """
    Daily OHLCV data for financial instruments.

    This table stores daily open, high, low, close, and volume data
    for various financial instruments (stocks, forex, crypto, etc.).
    """

    __tablename__ = "daily_ohlcv"

    # Composite primary key
    symbol = Column(
        String(20),
        primary_key=True,
        nullable=False,
        comment="Financial instrument symbol (e.g., AAPL, EURUSD)",
    )
    date = Column(Date, primary_key=True, nullable=False, comment="Trading date")

    # OHLCV data
    open = Column(Numeric(15, 4), nullable=False, comment="Opening price")
    high = Column(
        Numeric(15, 4), nullable=False, comment="Highest price during the trading day"
    )
    low = Column(
        Numeric(15, 4), nullable=False, comment="Lowest price during the trading day"
    )
    close = Column(Numeric(15, 4), nullable=False, comment="Closing price")
    volume = Column(BigInteger, nullable=False, comment="Trading volume")

    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"<DailyOHLCV(symbol='{self.symbol}', date={self.date}, "
            f"close={self.close}, volume={self.volume})>"
        )


class Symbol(Base, TimestampMixin):
    """
    Symbol metadata and configuration.

    This table stores metadata about financial instruments including
    their full names, asset classes, exchanges, and tracking status.
    """

    __tablename__ = "symbols"

    # Primary key
    symbol = Column(
        String(20),
        primary_key=True,
        nullable=False,
        comment="Financial instrument symbol (e.g., AAPL, EURUSD)",
    )

    # Metadata
    name = Column(
        String(255),
        nullable=True,
        comment="Full name of the instrument (e.g., 'Apple Inc.')",
    )
    asset_class = Column(
        String(50), nullable=False, comment="Asset class (equity, forex, crypto, etc.)"
    )
    exchange = Column(
        String(50), nullable=True, comment="Primary exchange (e.g., NASDAQ, NYSE)"
    )
    currency = Column(
        String(3), nullable=False, comment="Base currency (e.g., USD, EUR)"
    )

    # Status
    active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether symbol is actively tracked",
    )

    def __repr__(self) -> str:
        return (
            f"<Symbol(symbol='{self.symbol}', name='{self.name}', "
            f"asset_class='{self.asset_class}', active={self.active})>"
        )
