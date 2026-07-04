from bot.db.client import db
from bot.strategy.models import SignalCandidate
from bot.core.logger import logger

class StrategyRepository:
    @staticmethod
    def save_signal_candidate(signal: SignalCandidate):
        if not db.client:
            logger.warning("DB client not initialized, skipping signal save.")
            return
            
        try:
            data = {
                "symbol": signal.symbol,
                "signal_type": signal.signal_type,
                "timestamp": signal.timestamp,
                "price": signal.price
            }
            db.client.table("signal_candidates").insert(data).execute()
            logger.debug(f"Saved signal candidate to DB for {signal.symbol}")
        except Exception as e:
            logger.error(f"Error saving signal candidate: {e}")
