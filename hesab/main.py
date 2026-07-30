"""Main entry point for the Hesab Telegram Accounting Bot."""

import asyncio
import signal
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.config import settings
from app.utils.logger import logger
from app.database.models import init_database, close_database
from app.handlers.main_handler import router


async def set_bot_commands(bot: Bot):
    """Register bot commands with Telegram."""
    commands = [
        BotCommand(command="start", description="شروع ربات"),
        BotCommand(command="menu", description="منوی اصلی"),
        BotCommand(command="help", description="راهنما"),
        BotCommand(command="dashboard", description="داشبورد مالی"),
        BotCommand(command="report", description="گزارش‌های مالی"),
        BotCommand(command="backup", description="پشتیبان‌گیری"),
        BotCommand(command="search", description="جستجو"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Bot commands registered.")


def _cleanup_stale_exports():
    """Delete export files older than 1 hour from the exports directory."""
    import time
    export_dir = settings.EXPORT_DIR
    if not os.path.isdir(export_dir):
        return
    max_age = 3600  # 1 hour in seconds
    now = time.time()
    cleaned = 0
    for fname in os.listdir(export_dir):
        fpath = os.path.join(export_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            if now - os.path.getmtime(fpath) > max_age:
                os.remove(fpath)
                cleaned += 1
        except OSError:
            pass
    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} stale export files.")


async def main():
    """Initialize and start the bot."""
    # Validate configuration
    if not settings.is_valid:
        logger.error("Bot token is not configured! Please set BOT_TOKEN in .env file.")
        return

    if not settings.is_db_configured:
        logger.error("MongoDB URI is not configured! Please set MONGO_URI in .env file.")
        return

    # Initialize MongoDB connection at startup (with retries)
    import time
    for db_attempt in range(3):
        try:
            init_database()
            logger.info("MongoDB database initialized.")
            break
        except Exception as e:
            logger.warning(f"MongoDB attempt {db_attempt + 1}/3 failed: {e}")
            if db_attempt < 2:
                time.sleep(5)
            else:
                logger.critical(f"Failed to connect to MongoDB after 3 attempts: {e}")
                return

    # Clean up stale export files from previous runs
    _cleanup_stale_exports()

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Include routers
    dp.include_router(router)

    # Register bot commands
    await set_bot_commands(bot)

    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} started!")

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    async def _shutdown(sig_name: str):
        """Graceful shutdown handler."""
        logger.info(f"Received {sig_name}, shutting down gracefully...")
        await dp.storage.close()
        close_database()
        logger.info("Bot stopped and database connection closed.")

    def _signal_handler(sig_name: str):
        """Signal handler that schedules async shutdown."""
        logger.info(f"Signal {sig_name} received.")
        asyncio.ensure_future(_shutdown(sig_name))

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: _signal_handler(s.name))
        except NotImplementedError:
            # Windows does not support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler(signal.Signals(s).name))

    try:
        await dp.start_polling(bot)
    finally:
        close_database()
        logger.info("Bot stopped and database connection closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
