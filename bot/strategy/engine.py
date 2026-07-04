import pandas as pd
from typing import Optional
from bot.core.logger import logger
from bot.strategy.models import SignalCandidate

class StrategyEngine:
    def __init__(self):
        self.atr_buffer_mult = 1.5
        self.version = "2.0.0"
        self.name = "Consolidation_Breakout_MultiTF"
        
    def evaluate(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Optional[SignalCandidate]:
        if len(df_15m) < 25 or len(df_1h) < 1 or len(df_4h) < 1:
            return None
            
        latest_15m = df_15m.iloc[-1]
        latest_1h = df_1h.iloc[-1]
        latest_4h = df_4h.iloc[-1]
        
        # Ensure indicators exist
        req_cols = ['ema21', 'ema50', 'ema80', 'ema100', 'ema200', 'stochrsi_k', 'stochrsi_d', 'atr14']
        for col in req_cols:
            if col not in latest_15m or pd.isna(latest_15m[col]):
                return None
                
        # 1. Multi-Timeframe Bias
        htf_bias = "NEUTRAL"
        if not pd.isna(latest_1h.get('ema200')) and not pd.isna(latest_4h.get('ema200')):
            if latest_1h['close'] > latest_1h['ema200'] and latest_4h['close'] > latest_4h['ema200']:
                htf_bias = "LONG"
            elif latest_1h['close'] < latest_1h['ema200'] and latest_4h['close'] < latest_4h['ema200']:
                htf_bias = "SHORT"
                
        # 2. Check "Tight MAs" condition (max distance < 0.3% of price)
        mas = [latest_15m['ema21'], latest_15m['ema50'], latest_15m['ema80'], latest_15m['ema100']]
        max_ma = max(mas)
        min_ma = min(mas)
        ma_spread_pct = (max_ma - min_ma) / latest_15m['close']
        
        is_tight = ma_spread_pct < 0.005
        
        # 3. Consolidation logic
        # For a short: We look for a recent break below 200 EMA, and price staying below it
        recent_window = df_15m.iloc[-15:]
        
        # Check Short Setup
        short_setup = False
        reduced_risk = False
        tp_price = 0.0
        sl_price = 0.0
        
        is_below_200 = all(row['close'] < row['ema200'] for _, row in recent_window.iterrows())
        if is_below_200 and is_tight:
            short_setup = True
            reduced_risk = htf_bias == "LONG"
            
            # Measured move for TP
            # Look back 80 candles for swing high to capture the prior trend impulse
            recent_80 = df_15m.iloc[-80:]
            swing_high = recent_80['high'].max()
            swing_low = recent_window['low'].min()
            impulse = swing_high - swing_low
            tp_price = latest_15m['close'] - impulse
            
            sl_price = latest_15m['ema200'] + (latest_15m['atr14'] * self.atr_buffer_mult)
            
        # Check Long Setup
        long_setup = False
        is_above_200 = all(row['close'] > row['ema200'] for _, row in recent_window.iterrows())
        if not short_setup and is_above_200 and is_tight:
            long_setup = True
            reduced_risk = htf_bias == "SHORT"
            
            # Measured move for TP
            # Look back 80 candles for swing low to capture the prior trend impulse
            recent_80 = df_15m.iloc[-80:]
            swing_low = recent_80['low'].min()
            swing_high = recent_window['high'].max()
            impulse = swing_high - swing_low
            tp_price = latest_15m['close'] + impulse
            
            sl_price = latest_15m['ema200'] - (latest_15m['atr14'] * self.atr_buffer_mult)
            
        if not (short_setup or long_setup):
            return None
            

            
        signal_type = 'SHORT' if short_setup else 'LONG'
        symbol = latest_15m['symbol']
        entry_price = latest_15m['close']
        
        logger.info(f"Signal Generated: {signal_type} {symbol} @ {entry_price}, SL: {sl_price}, TP: {tp_price}, Reduced Risk: {reduced_risk}")
        
        return SignalCandidate(
            symbol=symbol,
            signal_type=signal_type,
            timestamp=latest_15m['timestamp'].item() if hasattr(latest_15m['timestamp'], 'item') else int(latest_15m['timestamp']),
            price=float(entry_price),
            stop_loss=float(sl_price),
            take_profit=float(tp_price),
            metadata={
                "strategy": self.name,
                "version": self.version,
                "htf_bias": htf_bias,
                "reduced_risk": reduced_risk,
                "ema200": float(latest_15m['ema200']),
                "stochrsi_k": float(latest_15m['stochrsi_k'])
            }
        )
