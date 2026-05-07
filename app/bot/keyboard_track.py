from telebot import types

from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_LYRICS,
    CB_UNFAVORITE,
    make_callback,
)
from app.localization.translations import t


def track_actions_keyboard(
    track: dict,
    is_favorite: bool = False,
    show_back_to_results: bool = False,
    language: str = "en",
) -> types.InlineKeyboardMarkup:
    """
    Creates inline keyboard under selected track card.
    Deezer and Spotify are displayed as URL buttons.
    Favorite button changes depending on current status.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    deezer_link = track.get("deezer_link")
    spotify_link = track.get("spotify_link")
    track_id = track.get("deezer_track_id")

    platform_buttons = []

    if deezer_link:
        platform_buttons.append(
            types.InlineKeyboardButton(
                text=t("btn_deezer", language),
                url=deezer_link,
            )
        )

    if spotify_link:
        platform_buttons.append(
            types.InlineKeyboardButton(
                text=t("btn_spotify", language),
                url=spotify_link,
            )
        )

    if platform_buttons:
        markup.row(*platform_buttons)

    if show_back_to_results:
        markup.add(
            types.InlineKeyboardButton(
                text=t("btn_back_results", language),
                callback_data=ACTION_BACK_RESULTS,
            )
        )

    if is_favorite:
        favorite_button = types.InlineKeyboardButton(
            text=t("btn_remove_favorites", language),
            callback_data=make_callback(CB_UNFAVORITE, track_id),
        )
    else:
        favorite_button = types.InlineKeyboardButton(
            text=t("btn_add_favorites", language),
            callback_data=make_callback(CB_FAVORITE, track_id),
        )

    markup.add(
        types.InlineKeyboardButton(
            text=t("btn_lyrics", language),
            callback_data=make_callback(CB_LYRICS, track_id),
        ),
        favorite_button,
    )

    markup.add(
        types.InlineKeyboardButton(
            text=t("btn_search_again", language),
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
