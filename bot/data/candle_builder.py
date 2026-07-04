from typing import List
from bot.data.models import Candle
from bot.core.logger import logger

class CandleBuilder:
    def __init__(self, timeframe_ms: int):
        self.timeframe_ms = timeframe_ms
        self.candles: List[Candle] = []
        
    def add_historical_candles(self, candles: List[Candle]):
        self.candles.extend(candles)
        # Ensure they are sorted and marked as closed
        self.candles.sort(key=lambda x: x.timestamp)
        for c in self.candles:
            c.closed = True

    def process_kline_update(self, symbol: str, timeframe: str, timestamp: int, 
                             open: float, high: float, low: float, close: float, 
                             volume: float, is_closed: bool) -> Candle | None:
        """
        Process a kline/candle update from a websocket or REST polling.
        Returns the closed candle if it just closed, else None.
        """
        candle = Candle(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            closed=is_closed
        )
        
        if not self.candles:
            self.candles.append(candle)
            return candle if is_closed else None
            
        last_candle = self.candles[-1]
        
        if timestamp > last_candle.timestamp:
            # New candle started, make sure last one is marked closed
            last_candle.closed = True
            self.candles.append(candle)
            return last_candle
        elif timestamp == last_candle.timestamp:
            # Update current candle
            self.candles[-1] = candle
            if is_closed:
                return candle
        
        return None
        
    def get_closed_candles(self) -> List[Candle]:
        return [c for c in self.candles if c.closed]
