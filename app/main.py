import asyncio

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent, FSInputFile

from app.bot.callbacks import router as callbacks_router
from app.bot.correlation_middleware import CorrelationMiddleware
from app.bot.handlers import router as handlers_router
from app.bot.shutdown_middleware import ShutdownMiddleware, drain_handlers
from app.config.settings import settings
from app.database.db import close_db_pool, init_db_pool
from app.monitoring import create_app
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger
from app.webhook import run_webhook_server, webhook_url

logger = setup_logger(__name__)

MONITORING_HOST = "0.0.0.0"
MONITORING_PORT = 9090


def create_bot() -> Bot:
    settings.validate()
    return Bot(token=settings.BOT_TOKEN)


async def handle_dispatcher_error(event: ErrorEvent) -> bool:
    """
    Global safety net for exceptions that escape a handler/callback unhandled
    (e.g. a DB hiccup during get_user_context, before any local try/except
    starts). Without this, aiogram logs internally and drops the update
    silently — no user feedback, no entry in the admin-visible errors table.

    Registered once on the Dispatcher's own `.errors` observer, which wraps
    the entire routing chain as an outer middleware (confirmed against the
    installed aiogram 3.29.0 source — ErrorsMiddleware is attached to
    dp.update, not per-router), so this catches escapes from every handler
    in every included router.
    """
    update = event.update
    telegram_id = None

    if update.message and update.message.from_user:
        telegram_id = update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        telegram_id = update.callback_query.from_user.id

    await log_and_save_error(
        logger=logger,
        telegram_id=telegram_id,
        source="dispatcher_error_handler",
        error=event.exception,
    )
    return True


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
    dp.errors.register(handle_dispatcher_error)
    dp.update.middleware(CorrelationMiddleware())
    dp.update.middleware(ShutdownMiddleware())

    dp.include_router(handlers_router)
    dp.include_router(callbacks_router)

    monitoring_server = _create_monitoring_server()
    monitoring_task = asyncio.create_task(monitoring_server.serve())
    task_sources = {monitoring_task: "monitoring_server"}

    logger.info("Bot started successfully.")

    source = "webhook_server" if settings.webhook_enabled else "start_polling"

    try:
        logger.info(
            "Monitoring server starting on %s:%s.",
            MONITORING_HOST,
            MONITORING_PORT,
        )

        # Polling and webhook are mutually exclusive at Telegram's API level
        # (an active webhook rejects getUpdates) — exactly one of them runs,
        # monitoring always runs alongside it. Two tasks either way.
        if settings.webhook_enabled:
            await bot.set_webhook(
                webhook_url(),
                certificate=FSInputFile(settings.WEBHOOK_CERT_PATH),
                secret_token=settings.WEBHOOK_SECRET_TOKEN,
                drop_pending_updates=True,
            )
            primary_task = asyncio.create_task(run_webhook_server(bot, dp))
            task_sources[primary_task] = "webhook_server"
            logger.info("Webhook server starting on port %s.", settings.WEBHOOK_PORT)
        else:
            await bot.delete_webhook(drop_pending_updates=True)
            primary_task = asyncio.create_task(dp.start_polling(bot))
            task_sources[primary_task] = "start_polling"

        done, pending = await asyncio.wait(
            set(task_sources),
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
        await drain_handlers(settings.SHUTDOWN_TIMEOUT_SECONDS)
        await bot.session.close()
        await close_db_pool()


def main() -> None:
    asyncio.run(run_bot())
