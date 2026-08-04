from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.utils.correlation import new_correlation_id, set_correlation_id


class CorrelationMiddleware(BaseMiddleware):
    """
    Assigns a short random correlation ID to every incoming Telegram update.
    The ID is stored in a ContextVar so it appears automatically in every
    log record emitted while that update is being handled.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        set_correlation_id(new_correlation_id())
        return await handler(event, data)
