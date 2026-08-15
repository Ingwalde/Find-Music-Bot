import json

from app.database.db import get_pool
from app.utils.types import TrackDict


async def get_cached_search(query_normalized: str, source: str) -> list[TrackDict] | None:
    """
    Returns cached search results if a fresh (<24h) entry exists, else None.
    Staleness is checked lazily on read via created_at — no active pruning.
    """
    async with (await get_pool()).acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT result_json
            FROM search_cache
            WHERE query_normalized = $1
              AND source = $2
              AND created_at > NOW() - INTERVAL '24 hours'
            """,
            query_normalized,
            source,
        )
    if not row:
        return None
    return json.loads(row["result_json"])


async def save_search_cache(query_normalized: str, source: str, results: list[TrackDict]) -> None:
    """
    Saves or replaces the cached search results for query_normalized + source.
    """
    result_json = json.dumps(results)

    async with (await get_pool()).acquire() as conn:
        await conn.execute(
            """
            INSERT INTO search_cache (query_normalized, source, result_json)
            VALUES ($1, $2, $3)
            ON CONFLICT (query_normalized, source)
            DO UPDATE SET
                result_json = EXCLUDED.result_json,
                created_at = NOW()
            """,
            query_normalized,
            source,
            result_json,
        )
