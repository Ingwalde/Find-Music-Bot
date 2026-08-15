from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ACTION_FAVORITES_CLEAR_CANCEL,
    ACTION_FAVORITES_CLEAR_CONFIRM,
    ACTION_FAVORITES_CLEAR_REQUEST,
    CB_TRACK,
    make_callback,
)
from app.localization.translations import t
from app.utils.text import truncate_text
from app.utils.types import TrackDict


def favorites_keyboard(
    tracks: list[TrackDict],
    language: str = "en",
) -> InlineKeyboardMarkup:
    """
    Creates improved favorites keyboard.
    """
    builder = InlineKeyboardBuilder()

    for track in tracks:
        title = track.get("title", "Unknown title")
        artist = track.get("artist", "Unknown artist")
        track_id = track.get("deezer_track_id")

        # Without an ID the callback would be "track:None", which matches
        # nothing — a button that silently does nothing when tapped. Skip it.
        if not track_id:
            continue

        button_text = truncate_text(f"🎵 {title} — {artist}", 64)

        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=make_callback(CB_TRACK, track_id),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_clear_favorites", language),
            callback_data=ACTION_FAVORITES_CLEAR_REQUEST,
        )
    )

    return builder.as_markup()


def confirm_clear_favorites_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """
    Confirmation keyboard for clearing all favorites.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_yes_clear", language),
            callback_data=ACTION_FAVORITES_CLEAR_CONFIRM,
        ),
        InlineKeyboardButton(
            text=t("btn_cancel", language),
            callback_data=ACTION_FAVORITES_CLEAR_CANCEL,
        ),
    )
    return builder.as_markup()
