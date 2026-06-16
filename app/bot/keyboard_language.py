from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.constants import CB_LANGUAGE, make_callback
from app.localization.languages import SUPPORTED_LANGUAGES, get_language_label


def language_keyboard() -> InlineKeyboardMarkup:
    """
    Creates language selection inline keyboard.
    """
    builder = InlineKeyboardBuilder()

    for language_code in SUPPORTED_LANGUAGES:
        builder.row(
            InlineKeyboardButton(
                text=get_language_label(language_code),
                callback_data=make_callback(CB_LANGUAGE, language_code),
            )
        )

    return builder.as_markup()
