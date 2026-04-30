from telebot import types

from app.utils.text import truncate_text
from app.bot.messages import BACK_TO_MENU_TEXT


def main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for main menu.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("music"))
    markup.add(
        types.KeyboardButton("favorites"),
        types.KeyboardButton("history"),
    )
    return markup


def back_to_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard with only Main menu button.
    Used in search, favorites and history screens.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(BACK_TO_MENU_TEXT))
    return markup


def search_mode_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard for music search mode.
    """
    return back_to_main_menu_keyboard()


def remove_keyboard() -> types.ReplyKeyboardRemove:
    """
    Removes bottom reply keyboard.
    """
    return types.ReplyKeyboardRemove()


def search_results_keyboard(
    tracks: list[dict],
    page: int = 0,
    total_pages: int = 1,
) -> types.InlineKeyboardMarkup:
    """
    Creates paginated inline keyboard with Deezer search results.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")

        button_text = truncate_text(f"{title} — {artist}", 64)

        markup.add(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"track:{track_id}",
            )
        )

    if total_pages > 1:
        navigation_buttons = []

        if page > 0:
            navigation_buttons.append(
                types.InlineKeyboardButton(
                    text="⬅️ Prev",
                    callback_data=f"page:{page - 1}",
                )
            )

        navigation_buttons.append(
            types.InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data="noop",
            )
        )

        if page < total_pages - 1:
            navigation_buttons.append(
                types.InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=f"page:{page + 1}",
                )
            )

        markup.row(*navigation_buttons)

    return markup


def track_actions_keyboard(
    track: dict,
    is_favorite: bool = False,
    show_back_to_results: bool = False,
) -> types.InlineKeyboardMarkup:
    """
    Creates inline keyboard under selected track card.
    Deezer is displayed as URL button.
    Favorite button changes depending on current status.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    deezer_link = track.get("deezer_link")
    track_id = track.get("deezer_track_id")

    if deezer_link:
        markup.add(
            types.InlineKeyboardButton(
                text="🎧 Deezer",
                url=deezer_link,
            )
        )

    if show_back_to_results:
        markup.add(
            types.InlineKeyboardButton(
                text="⬅️ Back to results",
                callback_data="back_results",
            )
        )

    if is_favorite:
        favorite_button = types.InlineKeyboardButton(
            text="❌ Remove from favorites",
            callback_data=f"unfav:{track_id}",
        )
    else:
        favorite_button = types.InlineKeyboardButton(
            text="⭐ Add to favorites",
            callback_data=f"fav:{track_id}",
        )

    markup.add(
        types.InlineKeyboardButton(
            text="📖 Lyrics",
            callback_data=f"lyrics:{track_id}",
        ),
        favorite_button,
    )

    markup.add(
        types.InlineKeyboardButton(
            text="🔎 Search again",
            callback_data="search_again",
        )
    )

    return markup


def genius_url_keyboard(url: str) -> types.InlineKeyboardMarkup:
    """
    Creates button for opening Genius lyrics page.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text="📖 Open lyrics on Genius",
            url=url,
        )
    )
    return markup


def favorites_keyboard(tracks: list[dict]) -> types.InlineKeyboardMarkup:
    """
    Creates improved favorites keyboard.
    User can open saved tracks, clear favorites or return to main menu.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")

        button_text = truncate_text(f"🎵 {title} — {artist}", 64)

        markup.add(
            types.InlineKeyboardButton(
                text=button_text,
                callback_data=f"track:{track_id}",
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            text="🗑 Clear favorites",
            callback_data="favorites_clear_request",
        )
    )

    return markup


def confirm_clear_favorites_keyboard() -> types.InlineKeyboardMarkup:
    """
    Confirmation keyboard for clearing all favorites.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            text="✅ Yes, clear",
            callback_data="favorites_clear_confirm",
        ),
        types.InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="favorites_clear_cancel",
        ),
    )
    return markup


def history_keyboard(history: list[dict]) -> types.InlineKeyboardMarkup:
    """
    Creates improved search history keyboard.
    User can repeat previous search, clear history or return to main menu.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for item in history:
        search_id = item.get("id")
        query = item.get("query", "Unknown query")

        markup.add(
            types.InlineKeyboardButton(
                text=truncate_text(f"🔎 {query}", 64),
                callback_data=f"hist:{search_id}",
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            text="🗑 Clear history",
            callback_data="history_clear_request",
        )
    )

    return markup


def confirm_clear_history_keyboard() -> types.InlineKeyboardMarkup:
    """
    Confirmation keyboard for clearing search history.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            text="✅ Yes, clear",
            callback_data="history_clear_confirm",
        ),
        types.InlineKeyboardButton(
            text="❌ Cancel",
            callback_data="history_clear_cancel",
        ),
    )
    return markup
