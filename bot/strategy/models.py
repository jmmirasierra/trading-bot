from pydantic import BaseModel
from typing import Optional, Dict, Any

class SignalCandidate(BaseModel):
    symbol: str
    signal_type: str # 'SHORT', 'LONG', 'EXIT'
    timestamp: int
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = {}
