from aiogram import Bot
from aiogram.types import CallbackQuery

from app.bot.keyboards import main_menu_keyboard
from app.config.admins import is_admin_user
from app.database.repositories import set_user_language, upsert_user
from app.localization.languages import is_supported_language
from app.localization.translations import t
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_language_callback(
    bot: Bot,
    call: CallbackQuery,
    language_code: str,
) -> None:
    """
    Saves selected language for current user.
    """
    # Narrowed once. The router rejects any callback whose message or
    # from_user is absent, so neither can be None here — binding them
    # keeps that in the type system instead of re-asserting per use.
    message = call.message
    user = call.from_user
    if message is None or user is None:
        return

    try:
        if not is_supported_language(language_code):
            await bot.answer_callback_query(
                call.id,
                t("unsupported_language", "en"),
                show_alert=True,
            )
            return

        await upsert_user(user)
        await set_user_language(user.id, language_code)

        await bot.answer_callback_query(call.id)

        await bot.send_message(
            message.chat.id,
            t("language_changed", language_code),
            reply_markup=main_menu_keyboard(
                language_code,
                is_admin=is_admin_user(user.id),
            ),
        )

    except Exception as error:
        await log_and_save_error(logger, user.id, "language_callback", error)
        await bot.answer_callback_query(call.id, t("unknown_action", "en"), show_alert=True)
