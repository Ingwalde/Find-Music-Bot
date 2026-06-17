from aiogram.types import User

from app.database.db import get_pool
from app.localization.languages import DEFAULT_LANGUAGE, is_supported_language


async def upsert_user(user: User) -> None:
    """
    Saves Telegram user or updates existing one.
    Existing language is preserved.
    """
    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, username, first_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name
            """,
            user.id,
            user.username,
            user.first_name,
        )


async def get_user_id(telegram_id: int) -> int | None:
    """
    Returns internal database user ID by Telegram ID.
    """
    async with (await get_pool()).acquire() as conn:
        result = await conn.fetchval(
            """
            SELECT id FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )

    if result is None:
        return None
    return int(result)


async def get_user_language(telegram_id: int | None) -> str:
    """
    Returns user's selected language.
    English is used as default/fallback.
    """
    if not telegram_id:
        return DEFAULT_LANGUAGE

    async with (await get_pool()).acquire() as conn:
        language = await conn.fetchval(
            """
            SELECT language
            FROM users
            WHERE telegram_id = $1
            LIMIT 1
            """,
            telegram_id,
        )

    if not language:
        return DEFAULT_LANGUAGE

    if not is_supported_language(language):
        return DEFAULT_LANGUAGE

    return language


async def set_user_language(telegram_id: int, language: str) -> None:
    """
    Saves user's selected language.
    """
    if not is_supported_language(language):
        language = DEFAULT_LANGUAGE

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET language = $1
            WHERE telegram_id = $2
            """,
            language,
            telegram_id,
        )


async def save_last_track_id(telegram_id: int, deezer_track_id: str) -> None:
    """
    Saves last viewed Deezer track ID for the user.
    """
    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            UPDATE users
            SET last_track_id = $1
            WHERE telegram_id = $2
            """,
            str(deezer_track_id),
            telegram_id,
        )


async def get_last_track_id(telegram_id: int) -> str | None:
    """
    Returns last viewed Deezer track ID for the user.
    """
    async with (await get_pool()).acquire() as conn:
        return await conn.fetchval(
            """
            SELECT last_track_id
            FROM users
            WHERE telegram_id = $1
            LIMIT 1
            """,
            telegram_id,
        )
