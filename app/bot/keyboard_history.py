from telebot import types

from app.bot.constants import (
    ACTION_HISTORY_CLEAR_CANCEL,
    ACTION_HISTORY_CLEAR_CONFIRM,
    ACTION_HISTORY_CLEAR_REQUEST,
    CB_HISTORY,
    make_callback,
)
from app.utils.text import truncate_text


def history_keyboard(history: list[dict]) -> types.InlineKeyboardMarkup:
    """
    Creates improved search history keyboard.
    User can repeat previous search or clear history.
    """
    markup = types.InlineKeyboardMarkup(row_width=1)

    for item in history:
        search_id = item.get("id")
        query = item.get("query", "Unknown query")

        markup.add(
            types.InlineKeyboardButton(
                text=truncate_text(f"🔎 {query}", 64),
                callback_data=make_callback(CB_HISTORY, search_id),
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            text="🗑 Clear history",
            callback_data=ACTION_HISTORY_CLEAR_REQUEST,
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
            callback_data=ACTION_HISTORY_CLEAR_CONFIRM,
        ),
        types.InlineKeyboardButton(
            text="❌ Cancel",
            callback_data=ACTION_HISTORY_CLEAR_CANCEL,
        ),
    )
    return markup
