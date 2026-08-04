import json

from app.database.db import get_pool
from app.database.repository_modules.common import row_to_dict


async def save_admin_audit(
    admin_telegram_id: int,
    action: str,
    details: dict | None = None,
) -> None:
    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO admin_audit (admin_telegram_id, action, details)
            VALUES ($1, $2, $3::jsonb)
            """,
            admin_telegram_id,
            action,
            json.dumps(details) if details is not None else None,
        )


async def get_recent_admin_audit(limit: int = 50) -> list[dict]:
    async with (await get_pool()).acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT admin_telegram_id, action, details, created_at
            FROM admin_audit
            ORDER BY id DESC
            LIMIT $1
            """,
            limit,
        )
    result = []
    for row in rows:
        d = row_to_dict(row)
        if isinstance(d.get("details"), str):
            d["details"] = json.loads(d["details"])
        result.append(d)
    return result
