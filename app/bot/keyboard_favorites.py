from telebot import types

from app.bot.constants import (
    ACTION_FAVORITES_CLEAR_CANCEL,
    ACTION_FAVORITES_CLEAR_CONFIRM,
    ACTION_FAVORITES_CLEAR_REQUEST,
    CB_TRACK,
    make_callback,
)
from app.localization.translations import t
from app.utils.text import truncate_text


def favorites_keyboard(
    tracks: list[dict],
    language: str = "en",
) -> types.InlineKeyboardMarkup:
    """
    Creates improved favorites keyboard.
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
                callback_data=make_callback(CB_TRACK, track_id),
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            text=t("btn_clear_favorites", language),
            callback_data=ACTION_FAVORITES_CLEAR_REQUEST,
        )
    )

    return markup


def confirm_clear_favorites_keyboard(language: str = "en") -> types.InlineKeyboardMarkup:
    """
    Confirmation keyboard for clearing all favorites.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            text=t("btn_yes_clear", language),
            callback_data=ACTION_FAVORITES_CLEAR_CONFIRM,
        ),
        types.InlineKeyboardButton(
            text=t("btn_cancel", language),
            callback_data=ACTION_FAVORITES_CLEAR_CANCEL,
        ),
    )
    return markup
