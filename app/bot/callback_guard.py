"""
Narrowing helpers for aiogram's optional CallbackQuery/Message fields.

Telegram omits `CallbackQuery.message` entirely when the message carrying the
button is older than roughly 48 hours, so `call.message` is genuinely None for
a user who scrolls back and taps a button on last week's track card. Every
callback in this package reached straight for `call.message.chat`, which raises
AttributeError in exactly that case — caught by the surrounding
`except Exception`, written to the errors table, and shown to the user as a
generic failure. 37 call sites had no guard at all.

`InaccessibleMessage` is not the problem: it carries both `chat` and
`message_id`. Only the None case is.

`from_user` is separately optional (None for channel posts), which is why
`require_user_id` exists alongside.
"""

from aiogram import Bot
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from app.localization.translations import t


def message_of(call: CallbackQuery) -> Message | InaccessibleMessage | None:
    """
    Returns the message a callback came from, or None when it is too old for
    Telegram to include. Both non-None variants expose chat and message_id.
    """
    return call.message


async def require_message(
    bot: Bot, call: CallbackQuery, language: str
) -> Message | InaccessibleMessage | None:
    """
    Returns the callback's message, or None after telling the user why nothing
    happened. Callers must return immediately on None.

    Uses the existing `search_session_expired` key rather than introducing a
    new one across eight locales — "the message this button belongs to is gone,
    start again" is the same thing the user needs to hear.
    """
    if call.message is None:
        await bot.answer_callback_query(
            call.id, t("search_session_expired", language), show_alert=True
        )
        return None

    return call.message


def require_user_id(call: CallbackQuery) -> int | None:
    """
    Returns the acting user's Telegram ID, or None when absent.

    aiogram types `from_user` as optional; for callback queries Telegram always
    populates it, so this is narrowing rather than a runtime concern — but it
    keeps the None out of the type system instead of silencing it per call site.
    """
    return call.from_user.id if call.from_user else None
