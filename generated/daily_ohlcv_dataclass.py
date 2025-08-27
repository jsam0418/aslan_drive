from dataclasses import dataclass
from datetime import date
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class DailyOhlcv:
    """
    Daily OHLCV data for financial instruments
    """
    symbol: str  # Financial instrument symbol
    date: datetime.date  # Trading date
    open: Decimal  # Opening price
    high: Decimal  # Highest price during the trading day
    low: Decimal  # Lowest price during the trading day
    close: Decimal  # Closing price
    volume: int  # Trading volume
    created_at: datetime.datetime  # Record creation timestamp