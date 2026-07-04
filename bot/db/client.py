from supabase import create_client, Client
from bot.config.settings import settings
from bot.core.logger import logger

class Database:
    def __init__(self):
        self.client: Client | None = None
        
    def connect(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            logger.warning("Supabase URL or Key not set. Database operations will fail.")
            return
            
        try:
            self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise

db = Database()
