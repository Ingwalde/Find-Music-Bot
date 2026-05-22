"""
Compatibility module for all keyboard builders.
"""

from app.bot.keyboard_favorites import (  # noqa: F401
    confirm_clear_favorites_keyboard,
    favorites_keyboard,
)
from app.bot.keyboard_history import (  # noqa: F401
    confirm_clear_history_keyboard,
    history_keyboard,
)
from app.bot.keyboard_language import language_keyboard  # noqa: F401
from app.bot.keyboard_menus import (  # noqa: F401
    admin_menu_keyboard,
    back_to_main_menu_keyboard,
    main_menu_keyboard,
    remove_keyboard,
    search_mode_keyboard,
)
from app.bot.keyboard_search import search_results_keyboard  # noqa: F401
from app.bot.keyboard_track import (  # noqa: F401
    genius_url_keyboard,
    track_actions_keyboard,
)
