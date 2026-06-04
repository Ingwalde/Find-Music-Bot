from telebot import types

from app.localization.translations import t


def main_menu_keyboard(language: str = "en", is_admin: bool = False) -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for main menu.
    Admin users get an additional Admin button.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(t("btn_music", language)))
    markup.add(
        types.KeyboardButton(t("btn_favorites", language)),
        types.KeyboardButton(t("btn_history", language)),
    )
    markup.add(types.KeyboardButton(t("btn_language", language)))

    if is_admin:
        markup.add(types.KeyboardButton(t("btn_admin", language)))

    return markup


def admin_menu_keyboard(language: str = "en") -> types.ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for admin maintenance actions.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(t("btn_admin_stats", language)),
        types.KeyboardButton(t("btn_admin_maintenance", language)),
    )
    markup.add(
        types.KeyboardButton(t("btn_admin_cleanup_errors", language)),
        types.KeyboardButton(t("btn_admin_cleanup_history", language)),
    )
    markup.add(
        types.KeyboardButton(t("btn_admin_health", language)),
        types.KeyboardButton(t("btn_admin_reload_admins", language)),
    )
    markup.add(types.KeyboardButton(t("btn_main_menu", language)))
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
