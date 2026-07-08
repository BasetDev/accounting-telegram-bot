"""Application configuration module."""

import os
from dotenv import load_dotenv

load_dotenv()

# Base directory: project root (where .env is located)
# __file__ is hesab/app/config.py, so BASE_DIR = project root (hesab/../)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_path(path: str) -> str:
    """Convert relative path to absolute path based on BASE_DIR."""
    if os.path.isabs(path):
        return path
    return os.path.join(BASE_DIR, path)


class Settings:
    """Application settings loaded from environment variables."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/hesab.db")

    APP_NAME: str = os.getenv("APP_NAME", "📊 حسابداری کسب‌وکار")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tehran")
    LANGUAGE: str = os.getenv("LANGUAGE", "fa")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hesab.log")

    BACKUP_DIR: str = _resolve_path(os.getenv("BACKUP_DIR", "backups"))
    EXPORT_DIR: str = _resolve_path(os.getenv("EXPORT_DIR", "exports"))
    UPLOAD_DIR: str = _resolve_path(os.getenv("UPLOAD_DIR", "uploads"))

    @property
    def is_valid(self) -> bool:
        """Check if the bot token is configured."""
        return bool(self.BOT_TOKEN) and self.BOT_TOKEN != "your_bot_token_here"


settings = Settings()