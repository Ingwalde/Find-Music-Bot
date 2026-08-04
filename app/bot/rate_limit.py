import asyncio
from collections import deque
from time import time

from app.config.settings import settings

_request_timestamps: dict[int, deque] = {}
_warned_users: set[int] = set()
_rate_limit_lock = asyncio.Lock()


async def check_rate_limit(telegram_id: int, *, is_admin: bool = False) -> bool:
    """
    Returns True if the request is allowed, False if the user has exceeded
    the sliding-window limit (RATE_LIMIT_MAX_REQUESTS per RATE_LIMIT_WINDOW_SECONDS).
    Admin users are always allowed through. In-memory only — resets on restart.
    """
    if is_admin:
        return True

    current_time = time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    async with _rate_limit_lock:
        timestamps = _request_timestamps.setdefault(telegram_id, deque())

        while timestamps and current_time - timestamps[0] > window:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            return False

        timestamps.append(current_time)
        _warned_users.discard(telegram_id)
        return True


async def should_warn_once(telegram_id: int) -> bool:
    """
    Returns True the first time a user is blocked within the current window,
    False on every subsequent blocked request — so the warning is sent once,
    not on every dropped request until the window clears.
    """
    async with _rate_limit_lock:
        if telegram_id in _warned_users:
            return False
        _warned_users.add(telegram_id)
        return True
