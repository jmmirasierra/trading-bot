import pandas as pd
import pandas_ta as ta
from typing import List
from bot.data.models import Candle
from bot.core.logger import logger

class IndicatorEngine:
    @staticmethod
    def calculate_indicators(candles: List[Candle]) -> pd.DataFrame:
        if len(candles) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame([c.model_dump() for c in candles])
        # Sort by timestamp to ensure correct calculation
        df = df.sort_values(by='timestamp').reset_index(drop=True)
        
        if len(df) < 200:
            logger.warning(f"Not enough candles for EMA200 calculation. Got {len(df)}, need at least 200.")
        
        # Calculate EMAs
        df['ema21'] = ta.ema(df['close'], length=21)
        df['ema50'] = ta.ema(df['close'], length=50)
        df['ema80'] = ta.ema(df['close'], length=80)
        df['ema100'] = ta.ema(df['close'], length=100)
        df['ema200'] = ta.ema(df['close'], length=200)
        
        # Calculate ATR14
        df['atr14'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Calculate ADX14
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None and not adx.empty:
            df['adx14'] = adx['ADX_14']
        else:
            df['adx14'] = pd.NA
            
        # Calculate RSI14 and StochRSI
        df['rsi14'] = ta.rsi(df['close'], length=14)
        stochrsi = ta.stochrsi(df['close'], length=14, rsi_length=14, k=3, d=3)
        if stochrsi is not None and not stochrsi.empty:
            df['stochrsi_k'] = stochrsi.iloc[:, 0]
            df['stochrsi_d'] = stochrsi.iloc[:, 1]
        else:
            df['stochrsi_k'] = pd.NA
            df['stochrsi_d'] = pd.NA
        
        # Swing High/Low using a rolling window approach
        window = 5
        df['swing_high'] = df['high'] == df['high'].rolling(window=window*2+1, center=True).max()
        df['swing_low'] = df['low'] == df['low'].rolling(window=window*2+1, center=True).min()
        
        return df
