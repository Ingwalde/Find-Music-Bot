from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ACTION_BACK_RESULTS,
    ACTION_SEARCH_AGAIN,
    CB_FAVORITE,
    CB_LYRICS,
    CB_SIMILAR,
    CB_UNFAVORITE,
    make_callback,
)
from app.localization.translations import t
from app.utils.types import TrackDict


def track_actions_keyboard(
    track: TrackDict,
    is_favorite: bool = False,
    show_back_to_results: bool = False,
    language: str = "en",
) -> InlineKeyboardMarkup:
    """
    Creates inline keyboard under selected track card.
    Deezer and Spotify are displayed as URL buttons.
    Favorite button changes depending on current status.
    """
    builder = InlineKeyboardBuilder()

    deezer_link = track.get("deezer_link")
    spotify_link = track.get("spotify_link")
    track_id = track.get("deezer_track_id")

    platform_buttons = []

    if deezer_link:
        platform_buttons.append(
            InlineKeyboardButton(
                text=t("btn_deezer", language),
                url=deezer_link,
            )
        )

    if spotify_link:
        platform_buttons.append(
            InlineKeyboardButton(
                text=t("btn_spotify", language),
                url=spotify_link,
            )
        )

    if platform_buttons:
        builder.row(*platform_buttons)

    if show_back_to_results:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_back_results", language),
                callback_data=ACTION_BACK_RESULTS,
            )
        )

    if track_id:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_similar", language),
                callback_data=make_callback(CB_SIMILAR, track_id),
            )
        )

    # All three track-scoped buttons need an ID. The Similar button above
    # already checked; lyrics and favourite did not, and rendered as
    # "lyrics:None" / "favorite:None" — visible, tappable, matching no handler.
    if track_id:
        builder.row(
            InlineKeyboardButton(
                text=t("btn_lyrics", language),
                callback_data=make_callback(CB_LYRICS, track_id),
            ),
            InlineKeyboardButton(
                text=t("btn_remove_favorites" if is_favorite else "btn_add_favorites", language),
                callback_data=make_callback(
                    CB_UNFAVORITE if is_favorite else CB_FAVORITE, track_id
                ),
            ),
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_search_again", language),
            callback_data=ACTION_SEARCH_AGAIN,
        )
    )

    return builder.as_markup()


def genius_url_keyboard(url: str, language: str = "en") -> InlineKeyboardMarkup:
    """
    Creates button for opening Genius lyrics page.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_open_genius", language),
            url=url,
        )
    )
    return builder.as_markup()
