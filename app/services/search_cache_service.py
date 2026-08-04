from app.database.repositories import get_cached_search, save_search_cache
from app.services.deezer_service import search_tracks
from app.utils.logger import setup_logger
from app.utils.metrics import search_cache_hits_total, search_cache_misses_total

logger = setup_logger(__name__)

SEARCH_CACHE_SOURCE = "deezer"


def normalize_query(query: str) -> str:
    """Normalizes a search query for cache-key matching (lowercase + trim)."""
    return query.strip().lower()


async def search_tracks_cached(query: str, limit: int) -> list[dict]:
    """
    Returns Deezer search results, using a 24h PostgreSQL cache keyed on the
    normalized query + source. Calls the Deezer API only on a cache miss or
    a stale (>24h) entry, then writes the fresh result back to the cache.
    """
    normalized = normalize_query(query)

    cached = await get_cached_search(normalized, SEARCH_CACHE_SOURCE)
    if cached is not None:
        logger.info("Search cache hit for %r", normalized)
        search_cache_hits_total.inc()
        return cached

    logger.info("Search cache miss for %r — calling Deezer", normalized)
    search_cache_misses_total.inc()
    tracks = await search_tracks(query=query, limit=limit)

    if tracks:
        await save_search_cache(normalized, SEARCH_CACHE_SOURCE, tracks)

    return tracks
