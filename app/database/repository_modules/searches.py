from app.config.settings import settings
from app.database.db import get_pool
from app.database.repository_modules.common import row_to_dict
from app.database.repository_modules.users import get_user_id


async def trim_search_history(telegram_id: int) -> None:
    """
    Keeps only newest MAX_HISTORY_PER_USER search rows for current user.
    """
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            DELETE FROM searches
            WHERE user_id = $1
            AND id NOT IN (
                SELECT id
                FROM searches
                WHERE user_id = $2
                ORDER BY id DESC
                LIMIT $3
            )
            """,
            user_id,
            user_id,
            settings.MAX_HISTORY_PER_USER,
        )


async def save_search(telegram_id: int, query: str) -> None:
    """
    Saves user's search query and trims old history rows.
    """
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    normalized_query = query.strip()

    if not normalized_query:
        return

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO searches (user_id, query)
            VALUES ($1, $2)
            """,
            user_id,
            normalized_query,
        )

    await trim_search_history(telegram_id)


async def get_search_history(telegram_id: int, limit: int = 10) -> list[dict]:
    """
    Returns recent unique search queries for user.
    The latest duplicate query is kept and older duplicates are hidden.
    """
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return []

    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT s.id, s.query, s.created_at
            FROM searches s
            JOIN (
                SELECT LOWER(TRIM(query)) AS normalized_query, MAX(id) AS latest_id
                FROM searches
                WHERE user_id = $1
                GROUP BY LOWER(TRIM(query))
            ) latest ON s.id = latest.latest_id
            WHERE s.user_id = $2
            ORDER BY s.id DESC
            LIMIT $3
            """,
            user_id,
            user_id,
            limit,
        )
    return [row_to_dict(row) for row in rows]


async def get_search_query_by_id(telegram_id: int, search_id: int) -> str | None:
    """
    Returns search query by history ID.
    Checks that the history item belongs to the current user.
    """
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return None

    async with (await get_pool()).acquire() as conn:
        val = await conn.fetchval(
            """
            SELECT query
            FROM searches
            WHERE id = $1
            AND user_id = $2
            LIMIT 1
            """,
            search_id,
            user_id,
        )

    return str(val) if val is not None else None


async def clear_search_history(telegram_id: int) -> None:
    """
    Clears current user's search history.
    """
    user_id = await get_user_id(telegram_id)

    if not user_id:
        return

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            DELETE FROM searches
            WHERE user_id = $1
            """,
            user_id,
        )
