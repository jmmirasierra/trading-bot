from typing import Optional
from bot.strategy.models import SignalCandidate
from bot.risk.manager import RiskManager
from bot.core.logger import logger
from bot.core.alerts import alerts
from bot.db.client import db

class ExecutionEngine:
    def __init__(self, mode: str = "PAPER"):
        self.mode = mode
        self.active_position = None
        
    async def execute_paper_trade(self, signal: SignalCandidate, position_size: float, risk_manager: RiskManager):
        logger.info(f"Executing PAPER trade for {signal.symbol}: {signal.signal_type} Size: {position_size}")
        
        entry_price = signal.price
        
        # Save order
        order_data = {
            "symbol": signal.symbol,
            "side": "SELL" if signal.signal_type == "SHORT" else "BUY",
            "order_type": "MARKET",
            "qty": position_size,
            "price": entry_price,
            "status": "FILLED"
        }
        
        if db.client:
            try:
                db.client.table("orders").insert(order_data).execute()
            except Exception as e:
                logger.error(f"Failed to save paper order: {e}")
                
        # Create Position state
        self.active_position = {
            "symbol": signal.symbol,
            "side": "SHORT" if signal.signal_type == "SHORT" else "LONG",
            "entry_price": entry_price,
            "qty": position_size,
            "sl": signal.stop_loss,
            "tp": signal.take_profit,
            "status": "OPEN"
        }
        
        if db.client:
            try:
                pos_data = {
                    "symbol": signal.symbol,
                    "side": self.active_position['side'],
                    "entry_price": entry_price,
                    "qty": position_size,
                    "status": "OPEN"
                }
                pos_res = db.client.table("positions").insert(pos_data).execute()
                self.active_position['id'] = pos_res.data[0]['id'] if pos_res.data else None
            except Exception as e:
                logger.error(f"Failed to save paper position: {e}")
                
        risk_manager.open_positions += 1
        await alerts.send_alert("Paper Trade Executed", f"Opened {self.active_position['side']} on {signal.symbol} at {entry_price}")
        
    async def update_paper_position(self, current_price: float, risk_manager: RiskManager):
        """
        Called on every tick/candle update to check SL/TP for paper trading.
        """
        if not self.active_position:
            return
            
        pos = self.active_position
        
        if pos['side'] == 'SHORT':
            if current_price >= pos['sl']:
                await self.close_paper_position(current_price, "STOP_LOSS", risk_manager)
            elif current_price <= pos['tp']:
                await self.close_paper_position(current_price, "TAKE_PROFIT", risk_manager)
                    
        elif pos['side'] == 'LONG':
            if current_price <= pos['sl']:
                await self.close_paper_position(current_price, "STOP_LOSS", risk_manager)
            elif current_price >= pos['tp']:
                await self.close_paper_position(current_price, "TAKE_PROFIT", risk_manager)
                
    async def close_paper_position(self, exit_price: float, reason: str, risk_manager: RiskManager):
        logger.info(f"Closing PAPER position due to {reason} at {exit_price}")
        
        pos = self.active_position
        pnl = (pos['entry_price'] - exit_price) * pos['qty'] if pos['side'] == 'SHORT' else (exit_price - pos['entry_price']) * pos['qty']
        
        if db.client and pos.get('id'):
            try:
                db.client.table("positions").update({"status": "CLOSED"}).eq("id", pos['id']).execute()
                trade_data = {
                    "position_id": pos['id'],
                    "realized_pnl": pnl,
                    "fees": 0.0 # simplified for paper
                }
                db.client.table("trades").insert(trade_data).execute()
            except Exception as e:
                logger.error(f"Failed to save paper trade exit: {e}")
                
        risk_manager.update_after_trade_closed(pnl)
        self.active_position = None
        risk_manager.open_positions = 0
        
        await alerts.send_alert("Paper Position Closed", f"Closed {pos['side']} on {pos['symbol']} at {exit_price}. PNL: {pnl:.2f} ({reason})")
