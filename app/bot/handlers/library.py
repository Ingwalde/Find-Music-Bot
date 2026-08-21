from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers._shared import get_user_context
from app.bot.keyboards import favorites_keyboard, history_keyboard, search_mode_keyboard
from app.config.settings import settings
from app.localization.translations import t
from app.services.favorites_service import get_favorite_tracks
from app.services.history_service import get_search_history
from app.services.user_service import get_user_language
from app.utils.error_logger import log_and_save_error
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = Router(name="handlers.library")


async def show_favorites(bot: Bot, message: Message) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    try:
        language = await get_user_context(message)

        await bot.send_message(
            message.chat.id,
            t("favorites_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        tracks = await get_favorite_tracks(user.id)

        if not tracks:
            await bot.send_message(message.chat.id, t("favorites_empty", language))
            return

        markup = favorites_keyboard(tracks, language)

        await bot.send_message(
            message.chat.id,
            t("favorites_title", language, count=len(tracks)),
            reply_markup=markup,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="favorites",
            error=error,
        )
        language = await get_user_language(user.id)
        await bot.send_message(message.chat.id, t("could_not_load_favorites", language))


async def show_history(bot: Bot, message: Message) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    try:
        language = await get_user_context(message)

        await bot.send_message(
            message.chat.id,
            t("history_menu", language),
            reply_markup=search_mode_keyboard(language),
        )

        history = await get_search_history(
            user.id,
            limit=settings.HISTORY_LIMIT,
        )

        if not history:
            await bot.send_message(message.chat.id, t("history_empty", language))
            return

        markup = history_keyboard(history, language)

        await bot.send_message(
            message.chat.id,
            t("history_title", language, count=len(history)),
            reply_markup=markup,
        )

    except Exception as error:
        await log_and_save_error(
            logger=logger,
            telegram_id=user.id,
            source="history",
            error=error,
        )
        language = await get_user_language(user.id)
        await bot.send_message(message.chat.id, t("could_not_load_history", language))


@router.message(Command("favorites"))
async def favorites_handler(message: Message, bot: Bot) -> None:
    await show_favorites(bot, message)


@router.message(Command("history"))
async def history_handler(message: Message, bot: Bot) -> None:
    await show_history(bot, message)
