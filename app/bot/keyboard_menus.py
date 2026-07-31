from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.localization.translations import t


def main_menu_keyboard(language: str = "en", is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for main menu.
    Admin users get an additional Admin button.
    """
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=t("btn_music", language)))
    builder.row(
        KeyboardButton(text=t("btn_favorites", language)),
        KeyboardButton(text=t("btn_history", language)),
    )
    builder.row(KeyboardButton(text=t("btn_language", language)))

    if is_admin:
        builder.row(KeyboardButton(text=t("btn_admin", language)))

    return builder.as_markup(resize_keyboard=True)


def admin_menu_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """
    Creates bottom reply keyboard for admin maintenance actions.
    """
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t("btn_admin_stats", language)),
        KeyboardButton(text=t("btn_admin_maintenance", language)),
    )
    builder.row(
        KeyboardButton(text=t("btn_admin_cleanup_errors", language)),
        KeyboardButton(text=t("btn_admin_cleanup_history", language)),
    )
    builder.row(
        KeyboardButton(text=t("btn_admin_health", language)),
        KeyboardButton(text=t("btn_admin_reload_admins", language)),
    )
    builder.row(KeyboardButton(text=t("btn_main_menu", language)))
    return builder.as_markup(resize_keyboard=True)


def back_to_main_menu_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """
    Creates bottom keyboard with only Main menu button.
    Used in search, favorites and history screens.
    """
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=t("btn_main_menu", language)))
    return builder.as_markup(resize_keyboard=True)


def search_mode_keyboard(language: str = "en") -> ReplyKeyboardMarkup:
    """
    Creates bottom keyboard for secondary screens and music search mode.
    """
    return back_to_main_menu_keyboard(language)
