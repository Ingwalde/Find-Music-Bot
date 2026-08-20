"""
Search history: recording queries, listing them, replaying one, clearing.

Owns the bot layer's access to the searches table. See user_service for why
these are re-exports rather than wrappers.
"""

from app.database.repositories import (
    clear_search_history,
    get_search_history,
    get_search_query_by_id,
    save_search,
)

__all__ = [
    "clear_search_history",
    "get_search_history",
    "get_search_query_by_id",
    "save_search",
]
