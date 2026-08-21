from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers._shared import get_user_context, is_admin
from app.bot.keyboards import language_keyboard, main_menu_keyboard
from app.localization.translations import t
from app.version import __version__

router = Router(name="handlers.common")


async def show_language_menu(bot: Bot, message: Message) -> None:
    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("choose_language", language),
        reply_markup=language_keyboard(),
    )


@router.message(Command("start"))
async def start_handler(message: Message, bot: Bot) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("welcome", language),
        reply_markup=main_menu_keyboard(language, is_admin=await is_admin(user.id)),
    )


@router.message(Command("help"))
async def help_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    await bot.send_message(message.chat.id, t("help", language))


@router.message(Command("language"))
async def language_handler(message: Message, bot: Bot) -> None:
    await show_language_menu(bot, message)


@router.message(Command("version"))
async def version_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    await bot.send_message(
        message.chat.id,
        t("version_info", language, version=__version__),
    )
