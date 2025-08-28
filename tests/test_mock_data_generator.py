"""
Tests for the mock data generator
"""
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.data_ingestion.mock_data_generator import MockOHLCVGenerator


def test_mock_generator_initialization():
    """Test mock generator initialization."""
    generator = MockOHLCVGenerator(seed=42)
    assert len(generator.symbols) > 0
    assert "AAPL" in generator.symbols
    assert generator.starting_prices["AAPL"] > 0


def test_generate_daily_ohlcv():
    """Test generation of single day OHLCV data."""
    generator = MockOHLCVGenerator(seed=42)
    test_date = date(2024, 1, 15)

    data = generator.generate_daily_ohlcv("AAPL", test_date)

    assert data["symbol"] == "AAPL"
    assert data["date"] == test_date
    assert isinstance(data["open"], Decimal)
    assert isinstance(data["high"], Decimal)
    assert isinstance(data["low"], Decimal)
    assert isinstance(data["close"], Decimal)
    assert isinstance(data["volume"], int)

    # Check logical relationships
    assert data["high"] >= data["open"]
    assert data["high"] >= data["close"]
    assert data["low"] <= data["open"]
    assert data["low"] <= data["close"]
    assert data["volume"] > 0


def test_generate_historical_data():
    """Test generation of historical data."""
    generator = MockOHLCVGenerator(seed=42)

    start_date = date(2024, 1, 1)
    end_date = date(2024, 1, 5)  # 5 days, but only weekdays should be included

    data = generator.generate_historical_data(
        symbols=["AAPL", "GOOGL"], start_date=start_date, end_date=end_date
    )

    # Should have data for weekdays only
    expected_weekdays = [
        d
        for d in [
            date(2024, 1, 1),  # Monday
            date(2024, 1, 2),  # Tuesday
            date(2024, 1, 3),  # Wednesday
            date(2024, 1, 4),  # Thursday
            date(2024, 1, 5),  # Friday
        ]
        if d.weekday() < 5
    ]

    expected_records = len(expected_weekdays) * 2  # 2 symbols
    assert len(data) == expected_records

    # Check that all records have required fields
    for record in data:
        assert "symbol" in record
        assert "date" in record
        assert "open" in record
        assert "high" in record
        assert "low" in record
        assert "close" in record
        assert "volume" in record


def test_generate_symbols_metadata():
    """Test generation of symbols metadata."""
    generator = MockOHLCVGenerator()
    metadata = generator.generate_symbols_metadata()

    assert len(metadata) > 0

    for item in metadata:
        assert "symbol" in item
        assert "name" in item
        assert "asset_class" in item
        assert "currency" in item
        assert "active" in item
        assert item["active"] is True  # All should be active


def test_price_evolution():
    """Test that prices evolve over time."""
    generator = MockOHLCVGenerator(seed=42)

    # Generate data for a few days
    dates = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    symbol = "AAPL"

    prices = []
    for test_date in dates:
        data = generator.generate_daily_ohlcv(symbol, test_date)
        prices.append(data["close"])

    # Prices should be different (random walk)
    assert not all(p == prices[0] for p in prices), "Prices should evolve over time"


def test_reproducible_with_seed():
    """Test that the same seed produces the same results."""
    gen1 = MockOHLCVGenerator(seed=123)
    gen2 = MockOHLCVGenerator(seed=123)

    test_date = date(2024, 1, 15)
    data1 = gen1.generate_daily_ohlcv("AAPL", test_date)
    data2 = gen2.generate_daily_ohlcv("AAPL", test_date)

    assert data1["open"] == data2["open"]
    assert data1["high"] == data2["high"]
    assert data1["low"] == data2["low"]
    assert data1["close"] == data2["close"]
    assert data1["volume"] == data2["volume"]
