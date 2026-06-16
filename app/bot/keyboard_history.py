from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import (
    ACTION_HISTORY_CLEAR_CANCEL,
    ACTION_HISTORY_CLEAR_CONFIRM,
    ACTION_HISTORY_CLEAR_REQUEST,
    CB_HISTORY,
    make_callback,
)
from app.localization.translations import t
from app.utils.text import truncate_text


def history_keyboard(
    history: list[dict],
    language: str = "en",
) -> InlineKeyboardMarkup:
    """
    Creates improved search history keyboard.
    """
    builder = InlineKeyboardBuilder()

    for item in history:
        search_id = item.get("id")
        query = item.get("query", "Unknown query")

        builder.row(
            InlineKeyboardButton(
                text=truncate_text(f"🔎 {query}", 64),
                callback_data=make_callback(CB_HISTORY, search_id),
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_clear_history", language),
            callback_data=ACTION_HISTORY_CLEAR_REQUEST,
        )
    )

    return builder.as_markup()


def confirm_clear_history_keyboard(language: str = "en") -> InlineKeyboardMarkup:
    """
    Confirmation keyboard for clearing search history.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=t("btn_yes_clear", language),
            callback_data=ACTION_HISTORY_CLEAR_CONFIRM,
        ),
        InlineKeyboardButton(
            text=t("btn_cancel", language),
            callback_data=ACTION_HISTORY_CLEAR_CANCEL,
        ),
    )
    return builder.as_markup()
