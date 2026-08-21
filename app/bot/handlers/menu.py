from aiogram import Bot, F, Router
from aiogram.types import Message

from app.bot.actions import ask_for_music, show_main_menu
from app.bot.handlers.admin import handle_admin_action, show_admin_menu
from app.bot.handlers.common import show_language_menu
from app.bot.handlers.library import show_favorites, show_history
from app.bot.handlers.search import process_music_search
from app.localization.translations import get_menu_action_by_text
from app.services.user_service import upsert_user

router = Router(name="handlers.menu")


@router.message(F.text)
async def text_handler(message: Message, bot: Bot) -> None:
    # from_user is Optional on the aiogram type (absent for channel
    # posts, which route elsewhere). Narrow once rather than per use.
    user = message.from_user
    if user is None:
        return

    await upsert_user(user)

    # Registered as @router.message(F.text), so text is present by the time
    # this runs — the filter is what guarantees it, not this check. Bind it so
    # the guarantee is visible to the type system too.
    text = message.text
    if not text:
        return

    if text.strip().startswith("/"):
        return

    action = get_menu_action_by_text(text)

    if action == "main_menu":
        await show_main_menu(bot, message.chat.id, user.id)
        return

    if action == "music":
        await ask_for_music(bot, message.chat.id, user.id)
        return

    if action == "favorites":
        await show_favorites(bot, message)
        return

    if action == "history":
        await show_history(bot, message)
        return

    if action == "language":
        await show_language_menu(bot, message)
        return

    if action == "admin":
        await show_admin_menu(bot, message)
        return

    if action in {
        "admin_stats",
        "admin_maintenance",
        "admin_cleanup_errors",
        "admin_cleanup_history",
        "admin_health",
        "admin_reload_admins",
    }:
        await handle_admin_action(bot, message, action)
        return

    await process_music_search(bot, message)
