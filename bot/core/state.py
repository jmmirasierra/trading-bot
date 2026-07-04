from enum import Enum
from bot.core.logger import logger

class BotState(Enum):
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class StateMachine:
    def __init__(self):
        self._state = BotState.INITIALIZING
        logger.info(f"Bot initialized in state: {self._state.value}")
    
    @property
    def current_state(self) -> BotState:
        return self._state
    
    def transition_to(self, new_state: BotState):
        logger.info(f"Transitioning from {self._state.value} to {new_state.value}")
        self._state = new_state
