from dataclasses import dataclass
from typing import Tuple, Optional
from bot.strategy.models import SignalCandidate
from bot.core.logger import logger

@dataclass
class RiskLimits:
    risk_per_trade_pct: float = 0.0050 # 0.50%
    max_daily_loss_pct: float = 0.0050 # 0.50%
    max_weekly_loss_pct: float = 0.0150 # 1.50%
    max_total_validation_loss_pct: float = 0.0300 # 3.00%
    max_trades_per_day: int = 2
    max_consecutive_losses: int = 2
    one_position_at_a_time: bool = True
    max_leverage: float = 3.0 # Maximum 3x leverage
    min_sl_dist_pct: float = 0.01 # 1.00% minimum SL distance to avoid fee drag
    min_rr_ratio: float = 3.0 # 3.0 minimum Reward-to-Risk ratio

class RiskManager:
    def __init__(self, initial_capital: float = 10000.0):
        self.limits = RiskLimits()
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # State tracking
        self.open_positions = 0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.total_pnl = 0.0
        self.trades_today = 0
        self.consecutive_losses = 0
        
    def evaluate_signal(self, signal: SignalCandidate) -> Tuple[bool, Optional[str], float]:
        """
        Evaluates a signal against all risk parameters.
        Returns: (Approved: bool, RejectionReason: str, PositionSize: float)
        """
        logger.info(f"RiskManager evaluating signal: {signal.symbol} {signal.signal_type}")
        
        # 1. Mandatory Stop Loss
        if signal.stop_loss is None:
            return False, "NO_STOP_LOSS", 0.0
            
        # 2. One position at a time
        if self.limits.one_position_at_a_time and self.open_positions >= 1:
            return False, "MAX_POSITIONS_REACHED", 0.0
            
        # 3. Max trades per day
        if self.limits.max_trades_per_day > 0 and self.trades_today >= self.limits.max_trades_per_day:
            return False, "MAX_DAILY_TRADES_REACHED", 0.0
            
        # 4. Max consecutive losses
        if self.limits.max_consecutive_losses > 0 and self.consecutive_losses >= self.limits.max_consecutive_losses:
            return False, "MAX_CONSECUTIVE_LOSSES_REACHED", 0.0
            
        # 5. Max daily loss
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= (self.current_capital * self.limits.max_daily_loss_pct):
            return False, "MAX_DAILY_LOSS_REACHED", 0.0
            
        # 6. Max weekly loss
        if self.weekly_pnl < 0 and abs(self.weekly_pnl) >= (self.current_capital * self.limits.max_weekly_loss_pct):
            return False, "MAX_WEEKLY_LOSS_REACHED", 0.0
            
        # 7. Max total validation loss
        if self.total_pnl < 0 and abs(self.total_pnl) >= (self.initial_capital * self.limits.max_total_validation_loss_pct):
            return False, "MAX_TOTAL_VALIDATION_LOSS_REACHED", 0.0
            
        # Position Sizing
        risk_amount = self.current_capital * self.limits.risk_per_trade_pct
        risk_per_unit = abs(signal.price - signal.stop_loss)
        
        if risk_per_unit == 0:
            return False, "ZERO_RISK_PER_UNIT", 0.0
            
        # 8. Check minimum Stop Loss distance to prevent fee drag
        sl_pct = risk_per_unit / signal.price
        if sl_pct < self.limits.min_sl_dist_pct:
            return False, "STOP_LOSS_TOO_TIGHT", 0.0
            
        # 9. Enforce minimum Reward-to-Risk ratio
        tp_dist = abs(signal.price - signal.take_profit)
        if (tp_dist / risk_per_unit) < self.limits.min_rr_ratio:
            return False, "RISK_REWARD_RATIO_TOO_LOW", 0.0
            
        position_size = risk_amount / risk_per_unit
        
        # 9. Enforce maximum leverage limit
        max_position_size = (self.current_capital * self.limits.max_leverage) / signal.price
        if position_size > max_position_size:
            logger.info(f"Capping position size due to max leverage limit ({self.limits.max_leverage}x). Reduced from {position_size} to {max_position_size}")
            position_size = max_position_size
        
        logger.info(f"RiskManager APPROVED signal. Size: {position_size}")
        return True, None, position_size
        
    def update_after_trade_closed(self, pnl: float):
        self.current_capital += pnl
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.total_pnl += pnl
        self.trades_today += 1
        
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
    def reset_daily(self):
        self.daily_pnl = 0.0
        self.trades_today = 0
        
    def reset_weekly(self):
        self.weekly_pnl = 0.0
