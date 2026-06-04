import telebot
from telebot import types

from app.bot.keyboards import main_menu_keyboard
from app.config.admins import is_admin_user
from app.database.repositories import set_user_language, upsert_user
from app.localization.languages import is_supported_language
from app.localization.translations import t


def handle_language_callback(
    bot: telebot.TeleBot,
    call: types.CallbackQuery,
    language_code: str,
) -> None:
    """
    Saves selected language for current user.
    """
    if not is_supported_language(language_code):
        bot.answer_callback_query(
            call.id,
            t("unsupported_language", "en"),
            show_alert=True,
        )
        return

    upsert_user(call.from_user)
    set_user_language(call.from_user.id, language_code)

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        t("language_changed", language_code),
        reply_markup=main_menu_keyboard(
            language_code,
            is_admin=is_admin_user(call.from_user.id),
        ),
    )
