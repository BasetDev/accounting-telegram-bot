"""Application configuration module."""

import os
from dotenv import load_dotenv

load_dotenv()

# Detect serverless environment (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

# Base directory: project root (where .env is located)
# __file__ is hesab/app/config.py, so BASE_DIR = project root (hesab/../)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_path(path: str) -> str:
    """Convert relative path to absolute path based on BASE_DIR."""
    if os.path.isabs(path):
        return path
    return os.path.join(BASE_DIR, path)


def _serverless_safe_path(env_key: str, default_relative: str) -> str:
    """Return a writable path. In serverless, redirect to /tmp.

    In Vercel/serverless environments, the filesystem is read-only except /tmp.
    This function ensures writable directories point to /tmp/hesab/ instead.
    """
    env_val = os.getenv(env_key, default_relative)
    resolved = _resolve_path(env_val)

    if IS_SERVERLESS:
        # Redirect to /tmp for serverless environments
        # Strip trailing slashes so basename() works correctly
        dirname = os.path.basename(resolved.rstrip(os.sep))
        if not dirname:
            dirname = default_relative.rstrip(os.sep)
        return os.path.join("/tmp", "hesab", dirname)

    return resolved


class Settings:
    """Application settings loaded from environment variables."""

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")

    # MongoDB Atlas Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "hesab")

    APP_NAME: str = os.getenv("APP_NAME", "📊 حسابداری کسب‌وکار")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tehran")
    LANGUAGE: str = os.getenv("LANGUAGE", "fa")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hesab.log")

    # In serverless, writable directories redirect to /tmp
    BACKUP_DIR: str = _serverless_safe_path("BACKUP_DIR", "backups")
    EXPORT_DIR: str = _serverless_safe_path("EXPORT_DIR", "exports")
    UPLOAD_DIR: str = _serverless_safe_path("UPLOAD_DIR", "uploads")

    @property
    def is_valid(self) -> bool:
        """Check if the bot token is configured."""
        return bool(self.BOT_TOKEN) and self.BOT_TOKEN != "your_bot_token_here"

    @property
    def is_db_configured(self) -> bool:
        """Check if MongoDB connection is configured."""
        return bool(self.MONGO_URI)


settings = Settings()