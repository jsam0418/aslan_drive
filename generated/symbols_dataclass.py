from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Symbols:
    """
    Symbol metadata and configuration
    """
    symbol: str  # Financial instrument symbol
    name: Optional[str] = None  # Full name of the instrument
    asset_class: str  # Asset class (equity, forex, crypto, etc.)
    exchange: Optional[str] = None  # Primary exchange
    currency: str  # Base currency
    active: bool  # Whether symbol is actively tracked
    created_at: datetime.datetime  # Record creation timestamp
    updated_at: datetime.datetime  # Record last updated timestamp