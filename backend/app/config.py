import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", os.getenv("RENDER_EXTERNAL_URL", "https://nekomini.onrender.com"))
    ADMIN_IDS_RAW: str = os.getenv("ADMIN_IDS", "123456789")
    STREAMER_NAME: str = os.getenv("STREAMER_NAME", "NekoMini Streamer")
    STREAMER_AVATAR: str = os.getenv("STREAMER_AVATAR", "")
    TWITCH_URL: str = os.getenv("TWITCH_URL", "https://twitch.tv/streamer")
    KICK_URL: str = os.getenv("KICK_URL", "https://kick.com/streamer")
    VK_URL: str = os.getenv("VK_URL", "https://live.vkvideo.ru/streamer")
    TELEGRAM_CHANNEL: str = os.getenv("TELEGRAM_CHANNEL", "https://t.me/streamer_channel")
    
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "True").lower() in ("true", "1", "t")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tma_streamer.db")
    
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_IDS_RAW:
            return []
        return [int(uid.strip()) for uid in self.ADMIN_IDS_RAW.split(",") if uid.strip().isdigit()]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
