from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.config.settings import settings
from app.database.db import get_pool
from app.platforms.spotify.auth import (
    get_spotify_block_reason,
    is_spotify_configured,
    is_spotify_temporarily_blocked,
)
from app.services.redis_client import get_redis_client


@dataclass(frozen=True)
class HealthItem:
    """
    Single diagnostic item for admin health checks.
    """

    name: str
    ok: bool
    message: str


async def check_database() -> HealthItem:
    """
    Checks whether the PostgreSQL database is reachable.
    """
    try:
        async with (await get_pool()).acquire() as conn:
            db_name = await conn.fetchval("SELECT current_database()")
        return HealthItem(
            name="Database",
            ok=True,
            message=f"OK ({db_name})",
        )
    except Exception as error:
        return HealthItem(
            name="Database",
            ok=False,
            message=f"Unavailable: {error}",
        )


def check_deezer() -> HealthItem:
    """
    Checks whether Deezer integration can be imported.

    This intentionally avoids a live network request, so /health stays fast and safe.
    """
    try:
        from app.services import deezer_service  # noqa: F401

        return HealthItem(name="Deezer", ok=True, message="Client import OK")
    except Exception as error:
        return HealthItem(name="Deezer", ok=False, message=f"Import failed: {error}")


def check_spotify() -> HealthItem:
    """
    Checks Spotify configuration and runtime cooldown state.
    """
    if not settings.SPOTIFY_ENABLED:
        return HealthItem(name="Spotify", ok=True, message="Disabled by configuration")

    if not is_spotify_configured():
        return HealthItem(name="Spotify", ok=True, message="Optional credentials are not configured")

    if is_spotify_temporarily_blocked():
        reason = get_spotify_block_reason() or "temporary cooldown"
        return HealthItem(name="Spotify", ok=False, message=f"Temporarily unavailable: {reason}")

    return HealthItem(name="Spotify", ok=True, message="Configured")


def check_genius() -> HealthItem:
    """
    Checks whether Genius lyrics lookup is configured.
    """
    if settings.GENIUS_TOKEN:
        return HealthItem(name="Genius", ok=True, message="Configured")

    return HealthItem(name="Genius", ok=True, message="Optional token is not configured")


async def check_redis() -> HealthItem:
    """
    Checks Redis connectivity. Skipped when REDIS_URL is not configured.
    """
    if not settings.REDIS_URL:
        return HealthItem(name="Redis", ok=True, message="Not configured (in-memory fallback active)")

    client = get_redis_client()
    if client is None:
        return HealthItem(name="Redis", ok=False, message="Client not initialised")

    try:
        await client.ping()
        return HealthItem(name="Redis", ok=True, message="OK")
    except Exception as error:
        return HealthItem(name="Redis", ok=False, message=f"Unavailable: {error}")


async def get_health_items() -> list[HealthItem]:
    """
    Returns health diagnostics used by the admin /health command.
    """
    # The two I/O checks run concurrently — a slow or timing-out database
    # should not add its latency to Redis's before the admin sees anything.
    database_item, redis_item = await asyncio.gather(check_database(), check_redis())

    return [
        HealthItem(name="Bot", ok=True, message="OK"),
        database_item,
        check_deezer(),
        check_spotify(),
        check_genius(),
        redis_item,
    ]


async def format_health_report() -> str:
    """
    Formats health diagnostics for Telegram.
    """
    lines = ["🩺 Find Music Bot health check"]

    for item in await get_health_items():
        icon = "✅" if item.ok else "⚠️"
        lines.append(f"{icon} {item.name}: {item.message}")

    return "\n".join(lines)
