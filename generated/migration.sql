-- Migration script generated from JSON schema
-- Schema version: 1.0.0
-- Generated at: 2025-08-27T20:30:53.535421

-- Create table: daily_ohlcv
CREATE TABLE IF NOT EXISTS daily_ohlcv (
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(15,4) NOT NULL,
    high DECIMAL(15,4) NOT NULL,
    low DECIMAL(15,4) NOT NULL,
    close DECIMAL(15,4) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_ohlcv_symbol_date ON daily_ohlcv (symbol, date);
CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_date ON daily_ohlcv (date);

-- Create table: symbols
CREATE TABLE IF NOT EXISTS symbols (
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    asset_class VARCHAR(50) NOT NULL,
    exchange VARCHAR(50),
    currency VARCHAR(3) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol)
);

CREATE INDEX IF NOT EXISTS idx_symbols_asset_class ON symbols (asset_class);
CREATE INDEX IF NOT EXISTS idx_symbols_active ON symbols (active);
