from telebot import types

from app.localization.translations import t


def main_menu_keyboard(language: str = "en") -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for main menu.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(t("btn_music", language)))
    markup.add(
        types.KeyboardButton(t("btn_favorites", language)),
        types.KeyboardButton(t("btn_history", language)),
    )
    markup.add(types.KeyboardButton(t("btn_language", language)))
    return markup


def back_to_main_menu_keyboard(language: str = "en") -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard with only Main menu button.
    Used in search, favorites and history screens.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(t("btn_main_menu", language)))
    return markup


def search_mode_keyboard(language: str = "en") -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard for secondary screens and music search mode.
    """
    return back_to_main_menu_keyboard(language)


def remove_keyboard() -> types.ReplyKeyboardRemove:
    """
    Removes bottom reply keyboard.
    """
    return types.ReplyKeyboardRemove()
