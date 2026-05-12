from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import settings
from app.database.db import get_connection, get_database_path
from app.platforms.spotify.auth import (
    get_spotify_block_reason,
    is_spotify_configured,
    is_spotify_temporarily_blocked,
)


@dataclass(frozen=True)
class HealthItem:
    """
    Single diagnostic item for admin health checks.
    """

    name: str
    ok: bool
    message: str


def check_database() -> HealthItem:
    """
    Checks whether the SQLite database is reachable.
    """
    try:
        db_path = get_database_path()

        with get_connection() as conn:
            conn.execute("SELECT 1")

        return HealthItem(
            name="Database",
            ok=True,
            message=f"OK ({Path(db_path).as_posix()})",
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


def get_health_items() -> list[HealthItem]:
    """
    Returns health diagnostics used by the admin /health command.
    """
    return [
        HealthItem(name="Bot", ok=True, message="OK"),
        check_database(),
        check_deezer(),
        check_spotify(),
        check_genius(),
    ]


def format_health_report() -> str:
    """
    Formats health diagnostics for Telegram.
    """
    lines = ["🩺 Find Music Bot health check"]

    for item in get_health_items():
        icon = "✅" if item.ok else "⚠️"
        lines.append(f"{icon} {item.name}: {item.message}")

    return "\n".join(lines)
