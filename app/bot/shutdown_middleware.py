import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)

# Single asyncio event loop — no race; increment/decrement only yield at `await`.
_in_flight: int = 0


class ShutdownMiddleware(BaseMiddleware):
    """
    Tracks in-flight handler invocations so drain_handlers() can wait for
    them to finish before the process closes the DB pool and bot session.
    Without this, a handler awaiting a DB call gets CancelledError mid-flight
    when the polling task is cancelled on SIGTERM.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        global _in_flight
        _in_flight += 1
        try:
            return await handler(event, data)
        finally:
            _in_flight -= 1


async def drain_handlers(timeout: float) -> None:
    """
    Waits up to `timeout` seconds for all in-flight handlers to complete.
    Called in run_bot()'s finally block, after the polling task is cancelled
    but before bot.session.close() and close_db_pool().
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while _in_flight > 0:
        if loop.time() >= deadline:
            logger.warning(
                "Shutdown drain timeout after %.0fs: %d handler(s) still in flight.",
                timeout,
                _in_flight,
            )
            return
        await asyncio.sleep(0.05)
    if timeout > 0:
        logger.info("Shutdown drain complete — all handlers finished.")
