import ccxt.async_support as ccxt
from typing import List
from bot.data.models import Candle
from bot.core.logger import logger

class MarketDataFetcher:
    def __init__(self, exchange_id: str = 'kucoinfutures'):
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,
            })
            logger.info(f"MarketDataFetcher initialized with exchange: {exchange_id}")
        except AttributeError:
            logger.error(f"Exchange {exchange_id} not found in CCXT")
            raise

    async def fetch_historical_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> List[Candle]:
        """
        Fetch historical candles.
        """
        try:
            ohlcvs = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            candles = []
            for ohlcv in ohlcvs:
                # CCXT format: [timestamp, open, high, low, close, volume]
                candle = Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=ohlcv[0],
                    open=ohlcv[1],
                    high=ohlcv[2],
                    low=ohlcv[3],
                    close=ohlcv[4],
                    volume=ohlcv[5],
                    closed=True # historical candles are considered closed
                )
                candles.append(candle)
            return candles
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return []
            
    async def close(self):
        if self.exchange:
            await self.exchange.close()
