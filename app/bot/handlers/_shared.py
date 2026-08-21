import asyncio

from aiogram import Bot
from aiogram.types import Message

from app.config.admins import is_admin_user
from app.config.settings import settings
from app.localization.languages import DEFAULT_LANGUAGE
from app.localization.translations import t
from app.services.admin_service import get_recent_errors, save_admin_audit
from app.services.user_service import get_user_language, upsert_user


async def is_admin(user_id: int | None) -> bool:
    return await asyncio.to_thread(is_admin_user, user_id)


async def get_user_context(message: Message) -> str:
    # from_user is Optional on the aiogram type (absent for channel posts,
    # which route elsewhere). With no user there is nobody to upsert and no
    # stored preference to read, so fall back to the default language rather
    # than inventing one.
    user = message.from_user
    if user is None:
        return DEFAULT_LANGUAGE

    await upsert_user(user)
    return await get_user_language(user.id)


async def require_admin(
    bot: Bot, message: Message, language: str, action: str | None = None
) -> bool:
    """
    Gate for admin-only commands. Returns True when the caller is an admin.

    Also writes the audit entry: menu actions were audited via
    handle_admin_action, but slash commands went through this gate and were
    never recorded, so an admin could run /stats, /clear_errors or
    /reload_admins with no audit trail at all. Auditing here covers every
    command that uses this gate, so a new admin command cannot silently skip
    it — pass `action` to name it.
    """
    # from_user is Optional on the aiogram type (absent for channel posts).
    # No identifiable user means no admin — deny, never fall through.
    user = message.from_user
    if user is None:
        return False

    if not await is_admin(user.id):
        await bot.send_message(message.chat.id, t("admin_only", language))
        return False

    if action:
        await save_admin_audit(user.id, action)

    return True


async def send_admin_only_message(bot: Bot, message: Message, language: str) -> None:
    await bot.send_message(message.chat.id, t("admin_only", language))


async def format_recent_errors(language: str = "en") -> str:
    errors = await get_recent_errors(limit=settings.ERROR_HISTORY_LIMIT)

    if not errors:
        return t("errors_empty", language)

    lines = [t("errors_header", language)]

    for index, item in enumerate(errors, start=1):
        source = item.get("source", "unknown")
        created_at = item.get("created_at", "unknown time")
        error_message = item.get("error_message", "Unknown error")
        telegram_id = item.get("telegram_id")

        user_part = f" | user: {telegram_id}" if telegram_id else ""
        lines.append(
            f"{index}. [{created_at}] {source}{user_part}\n"
            f"   {error_message}"
        )

    return "\n".join(lines)
