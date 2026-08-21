from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.admin_tools import (
    cleanup_errors_report,
    cleanup_history_report,
    format_maintenance_report,
    format_stats_report,
    reload_admins_report,
)
from app.bot.actions import send_long_message
from app.bot.handlers._shared import (
    format_recent_errors,
    get_user_context,
    is_admin,
    require_admin,
    send_admin_only_message,
)
from app.bot.keyboards import admin_menu_keyboard
from app.health import format_health_report
from app.localization.translations import t
from app.services.admin_service import clear_errors, save_admin_audit

router = Router(name="handlers.admin")


async def show_admin_menu(bot: Bot, message: Message) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)

    if not await is_admin(user.id):
        await send_admin_only_message(bot, message, language)
        return

    await bot.send_message(
        message.chat.id,
        t("admin_menu", language),
        reply_markup=admin_menu_keyboard(language),
    )


async def handle_admin_action(bot: Bot, message: Message, action: str) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    language = await get_user_context(message)
    admin_id = user.id

    if not await is_admin(admin_id):
        await send_admin_only_message(bot, message, language)
        return

    if action == "admin_stats":
        await send_long_message(bot, message.chat.id, await format_stats_report(language))
        await save_admin_audit(admin_id, action)
        return

    if action == "admin_maintenance":
        await send_long_message(bot, message.chat.id, await format_maintenance_report(language))
        await save_admin_audit(admin_id, action)
        return

    if action == "admin_cleanup_errors":
        await send_long_message(bot, message.chat.id, await cleanup_errors_report(language))
        await save_admin_audit(admin_id, action)
        return

    if action == "admin_cleanup_history":
        await send_long_message(bot, message.chat.id, await cleanup_history_report(language))
        await save_admin_audit(admin_id, action)
        return

    if action == "admin_health":
        await send_long_message(bot, message.chat.id, await format_health_report())
        await save_admin_audit(admin_id, action)
        return

    if action == "admin_reload_admins":
        # reload_admins_report only does in-memory lru_cache.cache_clear() — no DB I/O
        await bot.send_message(message.chat.id, reload_admins_report(language))
        await save_admin_audit(admin_id, action)


@router.message(Command("errors"))
async def errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_errors"):
        return

    await send_long_message(bot, message.chat.id, await format_recent_errors(language))


@router.message(Command("clear_errors"))
async def clear_errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_clear_errors"):
        return

    await clear_errors()
    await bot.send_message(message.chat.id, t("errors_cleared", language))


@router.message(Command("health"))
async def health_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_health"):
        return

    await send_long_message(bot, message.chat.id, await format_health_report())


@router.message(Command("stats"))
async def stats_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_stats"):
        return

    await send_long_message(bot, message.chat.id, await format_stats_report(language))


@router.message(Command("maintenance"))
async def maintenance_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_maintenance"):
        return

    await send_long_message(bot, message.chat.id, await format_maintenance_report(language))


@router.message(Command("cleanup_errors"))
async def cleanup_errors_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_cleanup_errors"):
        return

    await send_long_message(bot, message.chat.id, await cleanup_errors_report(language))


@router.message(Command("cleanup_history"))
async def cleanup_history_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_cleanup_history"):
        return

    await send_long_message(bot, message.chat.id, await cleanup_history_report(language))


@router.message(Command("reload_admins"))
async def reload_admins_handler(message: Message, bot: Bot) -> None:
    language = await get_user_context(message)

    if not await require_admin(bot, message, language, "cmd_reload_admins"):
        return

    await bot.send_message(message.chat.id, reload_admins_report(language))
