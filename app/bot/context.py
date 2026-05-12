from math import ceil

search_contexts: dict[int, dict] = {}


def save_search_context(user_id: int, query: str, tracks: list[dict]) -> None:
    """
    Saves last search results for user.
    Used for pagination without calling Deezer API again.
    """
    search_contexts[user_id] = {
        "query": query,
        "tracks": tracks,
        "page": 0,
    }


def get_search_context(user_id: int) -> dict | None:
    """
    Returns user's last search context.
    """
    return search_contexts.get(user_id)


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
