import os
import pandas as pd
from typing import List, Dict, Any
from bot.data.models import Candle
from bot.data.indicator import IndicatorEngine
from bot.strategy.engine import StrategyEngine
from bot.execution.backtester import BacktestEngine
from bot.core.logger import logger

def load_candles_from_csv(filepath: str, symbol: str, timeframe: str) -> List[Candle]:
    logger.info(f"Loading candles from {filepath} for {symbol}...")
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return []
    df = pd.read_csv(filepath)
    df = df[pd.to_numeric(df['open_time'], errors='coerce').notnull()]
    
    candles = []
    for _, row in df.iterrows():
        candles.append(Candle(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=int(float(row['open_time'])),
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=float(row['volume']),
            closed=True
        ))
    return candles

def resample_candles(df_15m: pd.DataFrame, rule: str) -> pd.DataFrame:
    df = df_15m.copy()
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'symbol': 'first'
    }).dropna().reset_index()
    
    resampled['timestamp'] = resampled['datetime'].astype('int64') // 10**6
    resampled.drop(columns=['datetime'], inplace=True)
    resampled['timeframe'] = rule
    resampled['closed'] = True
    return resampled

def df_to_candles(df: pd.DataFrame, timeframe: str) -> List[Candle]:
    return [
        Candle(
            symbol=row['symbol'],
            timeframe=timeframe,
            timestamp=int(row['timestamp']),
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=float(row['volume']),
            closed=True
        )
        for _, row in df.iterrows()
    ]

def run_backtest_for_period(name: str, files: List[str]):
    logger.info("=========================================")
    logger.info(f"RUNNING BACKTEST FOR {name}")
    logger.info("=========================================")
    
    candles_15m = []
    for f in files:
        candles_15m.extend(load_candles_from_csv(f, "BTCUSDT", "15m"))
        
    if not candles_15m:
        logger.error(f"No candles loaded for period {name}")
        return
        
    logger.info(f"Loaded total {len(candles_15m)} 15m candles for BTCUSDT {name}.")
    
    # Sort 15m candles by timestamp
    candles_15m.sort(key=lambda x: x.timestamp)
    
    df_15m_raw = pd.DataFrame([c.model_dump() for c in candles_15m])
    
    df_1h_raw = resample_candles(df_15m_raw, '1h')
    df_4h_raw = resample_candles(df_15m_raw, '4h')
    
    candles_1h = df_to_candles(df_1h_raw, '1h')
    candles_4h = df_to_candles(df_4h_raw, '4h')
    
    logger.info(f"DataFrame sizes for indicators - 15m: {len(df_15m_raw)}, 1h: {len(df_1h_raw)}, 4h: {len(df_4h_raw)}")
    
    df_15m = IndicatorEngine.calculate_indicators(candles_15m)
    df_1h = IndicatorEngine.calculate_indicators(candles_1h)
    df_4h = IndicatorEngine.calculate_indicators(candles_4h)
    
    strategy_engine = StrategyEngine()
    backtest_engine = BacktestEngine(strategy_engine)
    results = backtest_engine.run(df_15m, df_1h, df_4h)
    
    logger.info(f"=== BACKTEST RESULTS FOR BTCUSDT {name} ===")
    logger.info(f"initial_capital: {results.get('initial_capital')}")
    logger.info(f"final_capital: {results.get('final_capital')}")
    logger.info(f"net_profit: {results.get('net_profit')}")
    logger.info(f"total_trades: {results.get('total_trades')}")
    if results.get('total_trades', 0) > 0:
        logger.info(f"win_rate: {results.get('win_rate')}")
        logger.info(f"profit_factor: {results.get('profit_factor')}")
        logger.info(f"total_fees: {results.get('total_fees')}")
        logger.info(f"Trades details ({len(backtest_engine.trades)} trades):")
        for idx, t in enumerate(backtest_engine.trades, 1):
            logger.info(f"Trade {idx}: {t.side} | Entry: {t.entry_price:.2f} | Exit: {t.exit_price:.2f} | PnL: {t.pnl:.2f} | Status: {t.status}")
    else:
        logger.info("No trades executed.")

def main():
    base_dir = "/Users/jm_mirasierra/VisualStudioCode/Bot/btcusdt_klines_data"
    
    # Period 1: Jan-Apr 2024
    files_p1 = [
        f"{base_dir}/historico/BTCUSDT_15m_2024-01.csv",
        f"{base_dir}/historico/BTCUSDT_15m_2024-02.csv",
        f"{base_dir}/historico/BTCUSDT_15m_2024-03.csv",
        f"{base_dir}/historico/BTCUSDT_15m_2024-04.csv"
    ]
    
    # Period 2: May-Dec 2024
    files_p2 = [
        f"{base_dir}/BTCUSDT_15m_2024-05.csv",
        f"{base_dir}/BTCUSDT_15m_2024-06.csv",
        f"{base_dir}/BTCUSDT_15m_2024-07.csv",
        f"{base_dir}/BTCUSDT_15m_2024-08.csv",
        f"{base_dir}/BTCUSDT_15m_2024-09.csv",
        f"{base_dir}/BTCUSDT_15m_2024-10.csv",
        f"{base_dir}/BTCUSDT_15m_2024-11.csv",
        f"{base_dir}/BTCUSDT_15m_2024-12.csv"
    ]
    
    # Period 3: May 2025 - Apr 2026
    files_p3 = [
        f"{base_dir}/BTCUSDT_15m_2025-05.csv",
        f"{base_dir}/BTCUSDT_15m_2025-06.csv",
        f"{base_dir}/BTCUSDT_15m_2025-07.csv",
        f"{base_dir}/BTCUSDT_15m_2025-08.csv",
        f"{base_dir}/BTCUSDT_15m_2025-09.csv",
        f"{base_dir}/BTCUSDT_15m_2025-10.csv",
        f"{base_dir}/BTCUSDT_15m_2025-11.csv",
        f"{base_dir}/BTCUSDT_15m_2025-12.csv",
        f"{base_dir}/BTCUSDT_15m_2026-01.csv",
        f"{base_dir}/BTCUSDT_15m_2026-02.csv",
        f"{base_dir}/BTCUSDT_15m_2026-03.csv",
        f"{base_dir}/BTCUSDT_15m_2026-04.csv"
    ]
    
    run_backtest_for_period("2024 (Jan-Apr)", files_p1)
    run_backtest_for_period("2024 (May-Dec)", files_p2)
    run_backtest_for_period("2025-2026 (May-Apr)", files_p3)

if __name__ == "__main__":
    main()
