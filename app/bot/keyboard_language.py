from telebot import types

from app.bot.constants import CB_LANGUAGE, make_callback
from app.localization.languages import SUPPORTED_LANGUAGES, get_language_label


def language_keyboard() -> types.InlineKeyboardMarkup:
    """
    Creates language selection inline keyboard.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)

    for language_code in SUPPORTED_LANGUAGES:
        markup.add(
            types.InlineKeyboardButton(
                text=get_language_label(language_code),
                callback_data=make_callback(CB_LANGUAGE, language_code),
            )
        )

    return markup
