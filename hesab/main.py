"""Main entry point for the Hesab Telegram Accounting Bot."""

import asyncio
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
from app.database.models import init_database
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


async def main():
    """Initialize and start the bot."""
    # Validate configuration
    if not settings.is_valid:
        logger.error("Bot token is not configured! Please set BOT_TOKEN in .env file.")
        return

    # Initialize database at startup
    init_database()
    logger.info("Database initialized.")

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
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)