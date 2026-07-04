-- Candles
CREATE TABLE IF NOT EXISTS candles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp BIGINT NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    closed BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(symbol, timeframe, timestamp)
);

-- Strategy Instances
CREATE TABLE IF NOT EXISTS strategy_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    parameters JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Signal Candidates
CREATE TABLE IF NOT EXISTS signal_candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategy_instances(id),
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL, -- LONG, SHORT, EXIT
    timestamp BIGINT NOT NULL,
    price NUMERIC NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Risk Decisions
CREATE TABLE IF NOT EXISTS risk_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signal_candidates(id),
    approved BOOLEAN NOT NULL,
    rejection_reason TEXT,
    risk_pct NUMERIC,
    position_size NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange_order_id TEXT,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL, -- BUY, SELL
    order_type TEXT NOT NULL, -- MARKET, LIMIT, STOP
    qty NUMERIC NOT NULL,
    price NUMERIC,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Positions
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_price NUMERIC NOT NULL,
    qty NUMERIC NOT NULL,
    unrealized_pnl NUMERIC,
    status TEXT NOT NULL, -- OPEN, CLOSED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trades
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID REFERENCES positions(id),
    realized_pnl NUMERIC NOT NULL,
    fees NUMERIC NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bot Events
CREATE TABLE IF NOT EXISTS bot_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
