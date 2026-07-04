import ccxt.async_support as ccxt
from typing import Dict, Any, List
from bot.exchange.base import ExchangeAdapter
from bot.config.settings import settings
from bot.core.logger import logger

class KuCoinFuturesAdapter(ExchangeAdapter):
    def __init__(self, testnet: bool = True):
        self.exchange = ccxt.kucoinfutures({
            'apiKey': settings.KUCOIN_API_KEY,
            'secret': settings.KUCOIN_API_SECRET,
            'password': settings.KUCOIN_API_PASSPHRASE,
            'enableRateLimit': True,
        })
        if testnet:
            self.exchange.set_sandbox_mode(True)
            logger.info("KuCoinFuturesAdapter initialized in TESTNET mode.")
        else:
            logger.warning("KuCoinFuturesAdapter initialized in LIVE mode.")
            
    async def get_balance(self) -> float:
        balance = await self.exchange.fetch_balance()
        return float(balance.get('USDT', {}).get('free', 0.0))
        
    async def get_equity(self) -> float:
        balance = await self.exchange.fetch_balance()
        return float(balance.get('USDT', {}).get('total', 0.0))
        
    async def get_position(self, symbol: str) -> Dict[str, Any]:
        positions = await self.exchange.fetch_positions(symbols=[symbol])
        if positions and len(positions) > 0:
            return positions[0]
        return {}
        
    async def get_open_orders(self, symbol: str) -> List[Dict[str, Any]]:
        return await self.exchange.fetch_open_orders(symbol)
        
    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float = None, params: dict = None) -> Dict[str, Any]:
        params = params or {}
        # Enforce reduce-only logic if requested (usually passed in params for CCXT)
        return await self.exchange.create_order(symbol, order_type, side, qty, price, params)
        
    async def cancel_order(self, id: str, symbol: str) -> Dict[str, Any]:
        return await self.exchange.cancel_order(id, symbol)
        
    async def cancel_all_orders(self, symbol: str):
        return await self.exchange.cancel_all_orders(symbol)
        
    async def get_order_status(self, id: str, symbol: str) -> Dict[str, Any]:
        return await self.exchange.fetch_order(id, symbol)
