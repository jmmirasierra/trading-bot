from pydantic import BaseModel
from typing import Optional

class Candle(BaseModel):
    symbol: str
    timeframe: str
    timestamp: int # milliseconds
    open: float
    high: float
    low: float
    close: float
    volume: float
    closed: bool = False
