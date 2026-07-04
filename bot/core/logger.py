import sys
import os
from loguru import logger
from bot.config.settings import settings

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add("logs/bot.log", rotation="10 MB", retention="10 days", level="DEBUG")

__all__ = ["logger"]
