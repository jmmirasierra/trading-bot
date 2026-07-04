import pandas as pd
from typing import List, Dict, Any
from bot.strategy.engine import StrategyEngine
from bot.core.logger import logger

class Trade:
    def __init__(self, entry_price: float, sl: float, tp: float, timestamp: int, side: str, size: float):
        self.entry_price = entry_price
        self.sl = sl
        self.tp = tp
        self.entry_timestamp = timestamp
        self.exit_timestamp = None
        self.exit_price = None
        self.side = side
        self.initial_size = size
        self.current_size = size
        self.pnl = 0.0
        self.fees = 0.0
        self.status = 'OPEN'
        self.partials_taken = 0
        self.initial_risk = abs(entry_price - sl)   # 1R in price
        self.be_moved = False                        # SL already moved to breakeven
        self.partial_done = False                    # 50% partial exit executed

class BacktestEngine:
    def __init__(self, strategy_engine: StrategyEngine, initial_capital: float = 10000.0, fee_rate: float = 0.0006, slippage_pct: float = 0.0005):
        self.strategy = strategy_engine
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.fee_rate = fee_rate
        self.slippage_pct = slippage_pct
        self.trades: List[Trade] = []
        
    def run(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs the backtest loop over the 15m dataset, synced with 1H and 4H data.
        """
        logger.info(f"Starting backtest on {len(df_15m)} 15m candles, {len(df_1h)} 1h candles, {len(df_4h)} 4h candles.")
        
        open_trades: List[Trade] = []
        
        for i in range(200, len(df_15m)):
            window_15m = df_15m.iloc[:i]
            current_candle = window_15m.iloc[-1]
            timestamp = current_candle['timestamp']
            
            # Sync higher timeframes (ensure only fully closed candles are used to avoid lookahead bias)
            h1_ms = 3_600_000
            h4_ms = 14_400_000
            window_1h = df_1h[df_1h['timestamp'] + h1_ms <= timestamp]
            window_4h = df_4h[df_4h['timestamp'] + h4_ms <= timestamp]
            
            if len(window_1h) == 0 or len(window_4h) == 0:
                continue
                
            # Trade Management
            active_trades = []
            for trade in open_trades:
                if trade.status == 'OPEN':
                    low = current_candle['low']
                    high = current_candle['high']
                    
                    closed = False
                    if trade.side == 'SHORT':
                        if high >= trade.sl:
                            # Stop Loss hit
                            exit_price = trade.sl * (1 + self.slippage_pct)
                            self._close_trade(trade, exit_price, timestamp, is_partial=False)
                            closed = True
                        elif low <= trade.tp:
                            # Full Take Profit hit
                            exit_price = trade.tp * (1 - self.slippage_pct)
                            self._close_trade(trade, exit_price, timestamp, is_partial=False)
                            closed = True
                    elif trade.side == 'LONG':
                        if low <= trade.sl:
                            # Stop Loss hit
                            exit_price = trade.sl * (1 - self.slippage_pct)
                            self._close_trade(trade, exit_price, timestamp, is_partial=False)
                            closed = True
                        elif high >= trade.tp:
                            # Full Take Profit hit
                            exit_price = trade.tp * (1 + self.slippage_pct)
                            self._close_trade(trade, exit_price, timestamp, is_partial=False)
                            closed = True
                            
                    if not closed:
                        active_trades.append(trade)
            open_trades = active_trades
            
            # Evaluate strategy if we have room for more trades
            if len(open_trades) < 3:
                signal = self.strategy.evaluate(window_15m, window_1h, window_4h)
                
                if signal:
                    # Filter out signals too close to existing entries of the same side (1.5% distance minimum)
                    too_close = False
                    for trade in open_trades:
                        if trade.side == signal.signal_type:
                            dist = abs(signal.price - trade.entry_price) / trade.entry_price
                            if dist < 0.015:
                                too_close = True
                                break
                    if too_close:
                        continue

                    # Risk 0.5% flat per operation of total capital
                    risk_pct = 0.005
                    risk_amount = self.capital * risk_pct
                    
                    # Execute price with slippage
                    if signal.signal_type == 'SHORT':
                        entry_price = signal.price * (1 - self.slippage_pct)
                    else:
                        entry_price = signal.price * (1 + self.slippage_pct)
                        
                    risk_per_unit = abs(entry_price - signal.stop_loss)
                    if risk_per_unit == 0:
                        continue
                        
                    # Enforce minimum Stop Loss distance (1.0% of entry price) to avoid fee drag
                    sl_pct = risk_per_unit / entry_price
                    if sl_pct < 0.01:
                        continue
                        
                    # Enforce minimum Reward-to-Risk ratio of 3.0
                    tp_dist = abs(entry_price - signal.take_profit)
                    if (tp_dist / risk_per_unit) < 3.0:
                        continue
                        
                    position_size = risk_amount / risk_per_unit
                    
                    # Enforce maximum leverage (e.g. 3.0x capital)
                    max_position_size = (self.capital * 3.0) / entry_price
                    if position_size > max_position_size:
                        position_size = max_position_size
                    
                    trade = Trade(
                        entry_price=entry_price,
                        sl=signal.stop_loss,
                        tp=signal.take_profit,
                        timestamp=timestamp,
                        side=signal.signal_type,
                        size=position_size
                    )
                    self.trades.append(trade)
                    open_trades.append(trade)
                
        # Close any remaining open trades at the end of backtest
        for trade in open_trades:
            if trade.status == 'OPEN':
                self._close_trade(trade, df_15m.iloc[-1]['close'], df_15m.iloc[-1]['timestamp'], is_partial=False)
            
        return self._calculate_metrics()
        
    def _take_partial(self, trade: Trade, exit_price: float, timestamp: int, portion: float = 0.5):
        size_to_close = trade.current_size * portion
        trade.current_size -= size_to_close
        trade.partials_taken += 1
        
        entry_value = size_to_close * trade.entry_price
        exit_value = size_to_close * exit_price
        fees = (entry_value + exit_value) * self.fee_rate
        trade.fees += fees
        
        if trade.side == 'SHORT':
            pnl = (trade.entry_price - exit_price) * size_to_close - fees
        else:
            pnl = (exit_price - trade.entry_price) * size_to_close - fees
            
        trade.pnl += pnl
        self.capital += pnl
        logger.info(f"Partial TP taken for {trade.side} at {exit_price}. PNL secured: {pnl}")
        
        # Move Stop Loss to Break Even (entry price)
        trade.sl = trade.entry_price
        logger.info(f"Stop Loss moved to Break Even at {trade.sl}")

    def _close_trade(self, trade: Trade, exit_price: float, timestamp: int, is_partial: bool):
        trade.exit_price = exit_price
        trade.exit_timestamp = timestamp
        trade.status = 'CLOSED'
        
        size_to_close = trade.current_size
        if size_to_close <= 0: return
        
        entry_value = size_to_close * trade.entry_price
        exit_value = size_to_close * trade.exit_price
        fees = (entry_value + exit_value) * self.fee_rate
        trade.fees += fees
        
        if trade.side == 'SHORT':
            pnl = (trade.entry_price - trade.exit_price) * size_to_close - fees
        else:
            pnl = (trade.exit_price - trade.entry_price) * size_to_close - fees
            
        trade.pnl += pnl
        self.capital += pnl
        
    def _calculate_metrics(self) -> Dict[str, Any]:
        closed_trades = [t for t in self.trades if t.status == 'CLOSED']
        total_trades = len(closed_trades)
        
        if total_trades == 0:
            return {"total_trades": 0}
            
        winning_trades = [t for t in closed_trades if t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / total_trades
        gross_profit = sum([t.pnl for t in winning_trades])
        gross_loss = abs(sum([t.pnl for t in losing_trades]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        metrics = {
            "initial_capital": self.initial_capital,
            "final_capital": self.capital,
            "net_profit": self.capital - self.initial_capital,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_fees": sum([t.fees for t in closed_trades])
        }
        return metrics
