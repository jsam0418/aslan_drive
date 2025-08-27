from sqlalchemy import Column, String, Date, DateTime, Numeric, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Symbols(Base):
    """
    Symbol metadata and configuration
    """
    __tablename__ = "symbols"

    symbol = Column(String(20), primary_key=True, nullable=False)  # Financial instrument symbol
    name = Column(String(255))  # Full name of the instrument
    asset_class = Column(String(50), nullable=False)  # Asset class (equity, forex, crypto, etc.)
    exchange = Column(String(50))  # Primary exchange
    currency = Column(String(3), nullable=False)  # Base currency
    active = Column(Boolean, nullable=False, default=true)  # Whether symbol is actively tracked
    created_at = Column(DateTime, nullable=False, default=func.now())  # Record creation timestamp
    updated_at = Column(DateTime, nullable=False, default=func.now())  # Record last updated timestamp