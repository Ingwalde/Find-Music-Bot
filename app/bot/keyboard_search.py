from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import ACTION_NOOP, CB_PAGE, CB_TRACK, make_callback
from app.utils.text import truncate_text


def search_results_keyboard(
    tracks: list[dict],
    page: int = 0,
    total_pages: int = 1,
) -> InlineKeyboardMarkup:
    """
    Creates paginated inline keyboard with Deezer search results.
    """
    builder = InlineKeyboardBuilder()

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")
        button_text = truncate_text(f"{title} — {artist}", 64)

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=make_callback(CB_TRACK, track_id),
            )
        )

    if total_pages > 1:
        navigation_buttons = []

        if page > 0:
            navigation_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Prev",
                    callback_data=make_callback(CB_PAGE, page - 1),
                )
            )

        navigation_buttons.append(
            InlineKeyboardButton(
                text=f"📄 {page + 1}/{total_pages}",
                callback_data=ACTION_NOOP,
            )
        )

        if page < total_pages - 1:
            navigation_buttons.append(
                InlineKeyboardButton(
                    text="Next ➡️",
                    callback_data=make_callback(CB_PAGE, page + 1),
                )
            )

        builder.row(*navigation_buttons)

    return builder.as_markup()
