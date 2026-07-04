from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ExchangeAdapter(ABC):
    @abstractmethod
    async def get_balance(self) -> float:
        pass
        
    @abstractmethod
    async def get_equity(self) -> float:
        pass
        
    @abstractmethod
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float = None, params: dict = None) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def cancel_order(self, id: str, symbol: str) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def cancel_all_orders(self, symbol: str):
        pass
        
    @abstractmethod
    async def get_order_status(self, id: str, symbol: str) -> Dict[str, Any]:
        pass
