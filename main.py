import asyncio
from bot.config.settings import settings
from bot.core.logger import logger
from bot.core.state import StateMachine, BotState
from bot.db.client import db

async def main():
    logger.info("=========================================")
    logger.info("Starting Trading Bot (V1)")
    logger.info(f"Configured Mode: {settings.MODE}")
    logger.info(f"Live Trading Flag: {settings.LIVE_TRADING_ENABLED}")
    logger.info("=========================================")
    
    # 1. Initialize State Machine
    state_machine = StateMachine()
    
    # 2. Connect to Database (Supabase)
    db.connect()
    
    # 3. Security Check (Failsafe)
    if settings.MODE == "LIVE" and not settings.LIVE_TRADING_ENABLED:
        logger.error("CRITICAL: Attempted to start in LIVE mode but LIVE_TRADING_ENABLED is False.")
        logger.error("Aborting startup to prevent accidental live execution.")
        state_machine.transition_to(BotState.ERROR)
        return
        
    state_machine.transition_to(BotState.RUNNING)
    
    try:
        # Main Event Loop Placeholder
        # In a real scenario, this would initialize websockets, schedule polling, etc.
        while state_machine.current_state == BotState.RUNNING:
            logger.debug("Bot loop alive (Heartbeat)...")
            await asyncio.sleep(60) 
            
    except asyncio.CancelledError:
        logger.info("Async task cancelled.")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        state_machine.transition_to(BotState.ERROR)
    finally:
        state_machine.transition_to(BotState.STOPPING)
        # Ensure DB connections / Exchange sessions are closed here
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
