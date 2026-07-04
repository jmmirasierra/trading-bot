import aiohttp
import asyncio
from bot.core.logger import logger

class AlertManager:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        
    async def send_alert(self, title: str, message: str, level: str = "INFO"):
        logger_func = logger.info if level == "INFO" else logger.warning if level == "WARNING" else logger.error
        logger_func(f"ALERT [{title}]: {message}")
        
        if not self.webhook_url:
            return
            
        payload = {
            "content": f"**{title}**\n{message}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status not in (200, 204):
                        logger.error(f"Failed to send webhook alert: {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")

alerts = AlertManager()
