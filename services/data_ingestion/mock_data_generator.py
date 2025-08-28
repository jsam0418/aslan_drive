"""
Mock data generator for creating realistic OHLCV daily data
"""
import logging
import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockOHLCVGenerator:
    """Generates realistic mock OHLCV data for testing purposes."""

    def __init__(self, seed: int = 42):
        """Initialize the mock data generator with a random seed for reproducibility."""
        self.rng = random.Random(seed)
        self.symbols = [
            "AAPL",
            "GOOGL",
            "MSFT",
            "TSLA",
            "AMZN",
            "NVDA",
            "META",
            "NFLX",
            "SPY",
            "QQQ",
        ]

        # Starting prices for each symbol
        self.starting_prices = {
            "AAPL": Decimal("150.00"),
            "GOOGL": Decimal("2800.00"),
            "MSFT": Decimal("330.00"),
            "TSLA": Decimal("250.00"),
            "AMZN": Decimal("140.00"),
            "NVDA": Decimal("450.00"),
            "META": Decimal("320.00"),
            "NFLX": Decimal("400.00"),
            "SPY": Decimal("420.00"),
            "QQQ": Decimal("350.00"),
        }

        # Current prices (will be updated as we generate data)
        self.current_prices = self.starting_prices.copy()

    def generate_daily_ohlcv(self, symbol: str, trade_date: date) -> Dict[str, Any]:
        """Generate a single day's OHLCV data for a symbol."""
        if symbol not in self.current_prices:
            raise ValueError(f"Unknown symbol: {symbol}")

        # Get previous close (current price)
        prev_close = self.current_prices[symbol]

        # Generate daily volatility (typically 1-3% for most stocks)
        daily_volatility = self.rng.uniform(0.01, 0.03)

        # Random walk for the day's direction
        direction_change = self.rng.normalvariate(0, daily_volatility)

        # Calculate the day's range
        day_range = prev_close * Decimal(str(abs(direction_change)))

        # Generate OHLC with realistic relationships
        # Open: slightly different from previous close
        open_change = self.rng.uniform(-0.005, 0.005)  # ±0.5%
        open_price = prev_close * (1 + Decimal(str(open_change)))

        # Generate high and low based on the day's volatility
        high_range = day_range * Decimal(str(self.rng.uniform(0.5, 1.0)))
        low_range = day_range * Decimal(str(self.rng.uniform(0.5, 1.0)))

        if direction_change > 0:  # Up day
            close_price = prev_close * (1 + Decimal(str(direction_change)))
            high_price = max(open_price, close_price) + high_range
            low_price = min(open_price, close_price) - low_range * Decimal("0.3")
        else:  # Down day
            close_price = prev_close * (1 + Decimal(str(direction_change)))
            high_price = max(open_price, close_price) + high_range * Decimal("0.3")
            low_price = min(open_price, close_price) - low_range

        # Ensure logical relationships (high >= max(o,h,l,c), low <= min(o,h,l,c))
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        # Generate realistic volume (varies by symbol)
        base_volume = {
            "AAPL": 50_000_000,
            "GOOGL": 25_000_000,
            "MSFT": 30_000_000,
            "TSLA": 75_000_000,
            "AMZN": 35_000_000,
            "NVDA": 45_000_000,
            "META": 20_000_000,
            "NFLX": 8_000_000,
            "SPY": 80_000_000,
            "QQQ": 40_000_000,
        }

        volume_multiplier = self.rng.uniform(0.5, 2.0)  # Volume can vary significantly
        volume = int(base_volume.get(symbol, 10_000_000) * volume_multiplier)

        # Update current price for next day
        self.current_prices[symbol] = close_price

        # Round prices to appropriate precision
        open_price = open_price.quantize(Decimal("0.01"))
        high_price = high_price.quantize(Decimal("0.01"))
        low_price = low_price.quantize(Decimal("0.01"))
        close_price = close_price.quantize(Decimal("0.01"))

        return {
            "symbol": symbol,
            "date": trade_date,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "created_at": datetime.now(),
        }

    def generate_historical_data(
        self,
        symbols: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Generate historical OHLCV data for multiple symbols and date range."""
        if symbols is None:
            symbols = self.symbols

        if start_date is None:
            start_date = date.today() - timedelta(days=365)

        if end_date is None:
            end_date = date.today() - timedelta(days=1)  # Yesterday

        data = []
        current_date = start_date

        logger.info(
            f"Generating mock data for {len(symbols)} symbols from {start_date} to {end_date}"
        )

        while current_date <= end_date:
            # Skip weekends (assuming no trading)
            if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                for symbol in symbols:
                    ohlcv_data = self.generate_daily_ohlcv(symbol, current_date)
                    data.append(ohlcv_data)

            current_date += timedelta(days=1)

        logger.info(f"Generated {len(data)} data points")
        return data

    def generate_symbols_metadata(self) -> List[Dict[str, Any]]:
        """Generate metadata for the symbols."""
        metadata = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "TSLA",
                "name": "Tesla, Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "AMZN",
                "name": "Amazon.com, Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "NVDA",
                "name": "NVIDIA Corporation",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "META",
                "name": "Meta Platforms, Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "NFLX",
                "name": "Netflix, Inc.",
                "asset_class": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "asset_class": "etf",
                "exchange": "NYSE",
                "currency": "USD",
                "active": True,
            },
            {
                "symbol": "QQQ",
                "name": "Invesco QQQ Trust",
                "asset_class": "etf",
                "exchange": "NASDAQ",
                "currency": "USD",
                "active": True,
            },
        ]

        # Add timestamps
        now = datetime.now()
        for item in metadata:
            item["created_at"] = now
            item["updated_at"] = now

        return metadata
