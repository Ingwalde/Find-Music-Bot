import asyncio

from aiogram import Bot, Dispatcher

from app.bot.callbacks import router as callbacks_router
from app.bot.handlers import router as handlers_router
from app.config.settings import settings
from app.database.db import close_db_pool, init_db_pool
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_bot() -> Bot:
    settings.validate()
    return Bot(token=settings.BOT_TOKEN)


async def run_bot() -> None:
    await init_db_pool()

    bot = create_bot()
    dp = Dispatcher()

    dp.include_router(handlers_router)
    dp.include_router(callbacks_router)

    logger.info("Bot started successfully.")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=None,
            source="start_polling",
            error=error,
        )
        raise
    finally:
        await bot.session.close()
        await close_db_pool()


def main() -> None:
    asyncio.run(run_bot())
