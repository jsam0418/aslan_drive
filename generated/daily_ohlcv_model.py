from sqlalchemy import Column, String, Date, DateTime, Numeric, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class DailyOhlcv(Base):
    """
    Daily OHLCV data for financial instruments
    """
    __tablename__ = "daily_ohlcv"

    symbol = Column(String(20), primary_key=True, nullable=False)  # Financial instrument symbol
    date = Column(Date, primary_key=True, nullable=False)  # Trading date
    open = Column(Numeric(15,4), nullable=False)  # Opening price
    high = Column(Numeric(15,4), nullable=False)  # Highest price during the trading day
    low = Column(Numeric(15,4), nullable=False)  # Lowest price during the trading day
    close = Column(Numeric(15,4), nullable=False)  # Closing price
    volume = Column(BigInteger, nullable=False)  # Trading volume
    created_at = Column(DateTime, nullable=False, default=func.now())  # Record creation timestamp