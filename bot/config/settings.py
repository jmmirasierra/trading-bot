from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Exchange (KuCoin Futures)
    KUCOIN_API_KEY: str = ""
    KUCOIN_API_SECRET: str = ""
    KUCOIN_API_PASSPHRASE: str = ""

    # Bot Config
    MODE: Literal["BACKTEST", "PAPER", "DEMO", "LIVE"] = "PAPER"
    LIVE_TRADING_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
