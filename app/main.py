import telebot

from app.config.settings import settings
from app.database.db import init_db
from app.bot.handlers import register_handlers
from app.bot.callbacks import register_callbacks
from app.utils.logger import setup_logger


logger = setup_logger(__name__)


def create_bot() -> telebot.TeleBot:
    """
    Creates Telegram bot instance.
    """
    settings.validate()
    return telebot.TeleBot(settings.BOT_TOKEN)


def run_bot() -> None:
    """
    Initializes database, registers handlers and starts polling.
    """
    init_db()

    bot = create_bot()

    register_handlers(bot)
    register_callbacks(bot)

    logger.info("Bot started successfully.")

    bot.infinity_polling(
        timeout=60,
        long_polling_timeout=60,
        skip_pending=True,
    )
