"""Logging configuration module."""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from app.config import settings, IS_SERVERLESS


def setup_logger() -> logging.Logger:
    """Configure and return application logger.

    In serverless environments (Vercel/Lambda), only console logging is used
    since the filesystem is read-only. Logs appear in Vercel's function logs.
    """
    logger = logging.getLogger("hesab")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # Console handler (always active)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        "%(levelname)s: %(message)s"
    ))
    logger.addHandler(console_handler)

    # File handler only for non-serverless (VPS/PM2) deployments
    if not IS_SERVERLESS:
        try:
            log_dir = os.path.dirname(settings.LOG_FILE)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ))
            logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # Filesystem is read-only (serverless) — skip file logging
            pass

    return logger


logger = setup_logger()