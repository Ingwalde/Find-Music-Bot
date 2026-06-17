from app.database.db import get_pool
from app.database.repository_modules.common import row_to_dict


async def save_error(
    telegram_id: int | None,
    source: str,
    error_message: str,
) -> None:
    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO errors (telegram_id, source, error_message)
            VALUES ($1, $2, $3)
            """,
            telegram_id,
            source,
            error_message,
        )


async def get_recent_errors(limit: int = 10) -> list[dict]:
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT telegram_id, source, error_message, created_at
            FROM errors
            ORDER BY id DESC
            LIMIT $1
            """,
            limit,
        )
    return [row_to_dict(row) for row in rows]


async def clear_errors() -> None:
    async with (await get_pool()).acquire() as conn:
        await conn.execute("DELETE FROM errors")
