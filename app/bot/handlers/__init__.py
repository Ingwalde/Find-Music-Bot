"""
Message handlers, split by domain.

This was a single 640-line module — the largest in `app/` and the only one
that had grown into a god-module while `app/database/repository_modules/`
stayed neatly partitioned.

Each domain module owns its own `Router`; this package assembles them into the
one `router` that `app/main.py` includes, so the registration point outside
this package is unchanged.

    _shared   admin gate, user context, error formatting — used by every domain
    common    /start /help /language /version
    search    /similar /trending and free-text search
    library   /favorites /history
    admin     the admin menu and its eight commands
    menu      the reply-keyboard dispatcher

`menu` is separate rather than living in `common` because `text_handler` fans
out to every other domain — it is the reply-keyboard router, not a command.
Keeping it apart is what stops the domain modules importing each other.
"""

from aiogram import Router

from app.bot.handlers import _shared, admin, common, library, menu, search

# Re-exported so `app.bot.handlers.<name>` keeps working for callers and
# tests that predate the split into domain modules.
from app.bot.handlers._shared import (
    format_recent_errors,
    get_user_context,
    is_admin,
    require_admin,
    send_admin_only_message,
)
from app.bot.handlers.admin import (
    cleanup_errors_handler,
    cleanup_history_handler,
    clear_errors_handler,
    errors_handler,
    handle_admin_action,
    health_handler,
    maintenance_handler,
    reload_admins_handler,
    show_admin_menu,
    stats_handler,
)
from app.bot.handlers.common import (
    help_handler,
    language_handler,
    show_language_menu,
    start_handler,
    version_handler,
)
from app.bot.handlers.library import (
    favorites_handler,
    history_handler,
    show_favorites,
    show_history,
)
from app.bot.handlers.menu import text_handler
from app.bot.handlers.search import (
    process_music_search,
    similar_handler,
    trending_handler,
)

router = Router(name="handlers")

# Order matters: `menu` matches on F.text and would otherwise swallow text that
# a more specific router should see. It is included last for that reason.
router.include_router(common.router)
router.include_router(search.router)
router.include_router(library.router)
router.include_router(admin.router)
router.include_router(menu.router)

__all__ = [
    "_shared",
    "admin",
    "cleanup_errors_handler",
    "cleanup_history_handler",
    "clear_errors_handler",
    "common",
    "errors_handler",
    "favorites_handler",
    "format_recent_errors",
    "get_user_context",
    "handle_admin_action",
    "health_handler",
    "help_handler",
    "history_handler",
    "is_admin",
    "language_handler",
    "library",
    "maintenance_handler",
    "menu",
    "process_music_search",
    "reload_admins_handler",
    "require_admin",
    "router",
    "search",
    "send_admin_only_message",
    "show_admin_menu",
    "show_favorites",
    "show_history",
    "show_language_menu",
    "similar_handler",
    "start_handler",
    "stats_handler",
    "text_handler",
    "trending_handler",
    "version_handler",
]
