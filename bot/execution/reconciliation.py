from bot.exchange.base import ExchangeAdapter
from bot.core.logger import logger
from bot.core.alerts import alerts
from bot.core.state import StateMachine, BotState

class ReconciliationEngine:
    def __init__(self, exchange: ExchangeAdapter, state_machine: StateMachine):
        self.exchange = exchange
        self.state_machine = state_machine
        
    async def run_check(self, symbol: str, bot_expected_qty: float, bot_expected_side: str):
        """
        Compare bot state with exchange state.
        If mismatch, pause trading and alert.
        """
        try:
            position = await self.exchange.get_position(symbol)
            exchange_qty = float(position.get('contracts', 0.0))
            exchange_side = position.get('side', '') # 'short', 'long', or empty string if no pos
            
            mismatch = False
            error_details = ""
            
            if bot_expected_qty == 0 and exchange_qty > 0:
                mismatch = True
                error_details = f"Bot expects NO position, but Exchange has {exchange_qty} contracts."
                
            elif bot_expected_qty > 0:
                if exchange_qty == 0:
                    mismatch = True
                    error_details = "Bot expects OPEN position, but Exchange has none."
                elif abs(bot_expected_qty - exchange_qty) > 0.001:
                    mismatch = True
                    error_details = f"Size mismatch. Bot expects {bot_expected_qty}, Exchange has {exchange_qty}."
                elif bot_expected_side.lower() != exchange_side.lower():
                    mismatch = True
                    error_details = f"Direction mismatch. Bot expects {bot_expected_side}, Exchange has {exchange_side}."
                    
            if mismatch:
                logger.error(f"RECONCILIATION MISMATCH: {error_details}")
                await alerts.send_alert("CRITICAL: Reconciliation Mismatch", error_details, level="ERROR")
                self.state_machine.transition_to(BotState.PAUSED)
                logger.warning("Bot has been PAUSED due to reconciliation failure.")
            else:
                logger.debug("Reconciliation check passed.")
                
        except Exception as e:
            logger.error(f"Error during reconciliation check: {e}")
