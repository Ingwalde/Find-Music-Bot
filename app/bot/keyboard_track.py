from telebot import types

from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_LYRICS,
    CB_UNFAVORITE,
    make_callback,
)


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
                callback_data=ACTION_BACK_RESULTS,
            )
        )

    if is_favorite:
        favorite_button = types.InlineKeyboardButton(
            text="❌ Remove from favorites",
            callback_data=make_callback(CB_UNFAVORITE, track_id),
        )
    else:
        favorite_button = types.InlineKeyboardButton(
            text="⭐ Add to favorites",
            callback_data=make_callback(CB_FAVORITE, track_id),
        )

    markup.add(
        types.InlineKeyboardButton(
            text="📖 Lyrics",
            callback_data=make_callback(CB_LYRICS, track_id),
        ),
        favorite_button,
    )

    markup.add(
        types.InlineKeyboardButton(
            text="🔎 Search again",
            callback_data=ACTION_SEARCH_AGAIN,
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
