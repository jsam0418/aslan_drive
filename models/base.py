"""
Base SQLAlchemy configuration for Aslan Drive
"""
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class TimestampMixin:
    """Mixin class to add timestamp columns to models."""
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=func.now(), 
        onupdate=func.now()
    )