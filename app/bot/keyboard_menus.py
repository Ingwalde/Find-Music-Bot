from telebot import types

from app.bot.constants import (
    BTN_FAVORITES,
    BTN_HISTORY,
    BTN_MAIN_MENU,
    BTN_MUSIC,
)


def main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for main menu.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(BTN_MUSIC))
    markup.add(
        types.KeyboardButton(BTN_FAVORITES),
        types.KeyboardButton(BTN_HISTORY),
    )
    return markup


def back_to_main_menu_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard with only Main menu button.
    Used in search, favorites and history screens.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(BTN_MAIN_MENU))
    return markup


def search_mode_keyboard() -> types.ReplyKeyboardMarkup:
    """
    Creates bottom keyboard for secondary screens and music search mode.
    """
    return back_to_main_menu_keyboard()


def remove_keyboard() -> types.ReplyKeyboardRemove:
    """
    Removes bottom reply keyboard.
    """
    return types.ReplyKeyboardRemove()
