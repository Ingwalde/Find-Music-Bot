import asyncio

import uvicorn
from aiogram import Bot, Dispatcher

from app.bot.callbacks import router as callbacks_router
from app.bot.handlers import router as handlers_router
from app.config.settings import settings
from app.database.db import close_db_pool, init_db_pool
from app.monitoring import create_app
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

MONITORING_HOST = "0.0.0.0"
MONITORING_PORT = 9090


def create_bot() -> Bot:
    settings.validate()
    return Bot(token=settings.BOT_TOKEN)


def _create_monitoring_server() -> uvicorn.Server:
    config = uvicorn.Config(
        create_app(),
        host=MONITORING_HOST,
        port=MONITORING_PORT,
        log_config=None,
    )
    return uvicorn.Server(config)


async def run_bot() -> None:
    await init_db_pool()

    bot = create_bot()
    dp = Dispatcher()

    dp.include_router(handlers_router)
    dp.include_router(callbacks_router)

    monitoring_server = _create_monitoring_server()

    logger.info("Bot started successfully.")

    source = "start_polling"

    try:
        await bot.delete_webhook(drop_pending_updates=True)

        polling_task = asyncio.create_task(dp.start_polling(bot))
        monitoring_task = asyncio.create_task(monitoring_server.serve())
        task_sources = {
            polling_task: "start_polling",
            monitoring_task: "monitoring_server",
        }

        logger.info(
            "Monitoring server starting on %s:%s.",
            MONITORING_HOST,
            MONITORING_PORT,
        )

        done, pending = await asyncio.wait(
            {polling_task, monitoring_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        for task in done:
            error = task.exception()
            if error is not None:
                source = task_sources[task]
                raise error
    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=None,
            source=source,
            error=error,
        )
        raise
    finally:
        await bot.session.close()
        await close_db_pool()


def main() -> None:
    asyncio.run(run_bot())
