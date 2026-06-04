from math import ceil
from time import time

SEARCH_CONTEXT_TTL_SECONDS = 60 * 60

search_contexts: dict[int, dict] = {}


def cleanup_expired_search_contexts(now: float | None = None) -> int:
    """
    Removes expired in-memory search contexts and returns the number of removed entries.
    """
    current_time = time() if now is None else now
    expired_user_ids = [
        user_id
        for user_id, context in search_contexts.items()
        if current_time - float(context.get("created_at", 0)) > SEARCH_CONTEXT_TTL_SECONDS
    ]

    for user_id in expired_user_ids:
        search_contexts.pop(user_id, None)

    return len(expired_user_ids)


def clear_search_context(user_id: int) -> None:
    """
    Removes one user's search context.
    """
    search_contexts.pop(user_id, None)


def save_search_context(user_id: int, query: str, tracks: list[dict]) -> None:
    """
    Saves last search results for user.
    Used for pagination without calling Deezer API again.
    """
    cleanup_expired_search_contexts()
    search_contexts[user_id] = {
        "query": query,
        "tracks": tracks,
        "page": 0,
        "created_at": time(),
    }


def get_search_context(user_id: int) -> dict | None:
    """
    Returns user's last search context.
    Expired contexts are removed lazily to avoid unbounded memory growth.
    """
    context = search_contexts.get(user_id)

    if not context:
        return None

    created_at = float(context.get("created_at", 0))

    if time() - created_at > SEARCH_CONTEXT_TTL_SECONDS:
        clear_search_context(user_id)
        return None

    return context


def get_total_pages(user_id: int, page_size: int) -> int:
    """
    Returns total number of pages for user's last search.
    """
    context = get_search_context(user_id)

    if not context:
        return 0

    tracks = context.get("tracks", [])

    if not tracks:
        return 0

    return max(1, ceil(len(tracks) / page_size))


def set_search_page(user_id: int, page: int, page_size: int) -> int:
    """
    Sets current page safely and returns normalized page number.
    """
    context = get_search_context(user_id)

    if not context:
        return 0

    total_pages = get_total_pages(user_id, page_size)

    if total_pages <= 0:
        context["page"] = 0
        return 0

    normalized_page = max(0, min(page, total_pages - 1))
    context["page"] = normalized_page
    return normalized_page


def get_current_page(user_id: int) -> int:
    """
    Returns current page number for user's last search.
    """
    context = get_search_context(user_id)

    if not context:
        return 0

    return int(context.get("page", 0))


def get_page_tracks(user_id: int, page_size: int, page: int | None = None) -> list[dict]:
    """
    Returns tracks for selected page.
    """
    context = get_search_context(user_id)

    if not context:
        return []

    tracks = context.get("tracks", [])

    if page is None:
        page = get_current_page(user_id)

    start = page * page_size
    end = start + page_size

    return tracks[start:end]
