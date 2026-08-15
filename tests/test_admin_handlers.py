import pytest

from app.bot import handlers
from tests.conftest import AsyncFakeBot, fake_message, to_async


@pytest.mark.asyncio
async def test_admin_handlers_return_admin_reports(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: user_id == 123)
    monkeypatch.setattr(handlers, "format_stats_report", to_async(lambda language="en": "stats report"))
    monkeypatch.setattr(
        handlers, "format_maintenance_report", to_async(lambda language="en": "maintenance report")
    )
    monkeypatch.setattr(
        handlers, "cleanup_errors_report", to_async(lambda language="en": "errors cleanup")
    )
    monkeypatch.setattr(
        handlers, "cleanup_history_report", to_async(lambda language="en": "history cleanup")
    )

    audited: list[tuple[int, str]] = []
    monkeypatch.setattr(
        handlers,
        "save_admin_audit",
        to_async(lambda admin_id, action: audited.append((admin_id, action))),
    )

    msg = fake_message(user_id=123)
    await handlers.stats_handler(msg, bot)
    await handlers.maintenance_handler(msg, bot)
    await handlers.cleanup_errors_handler(msg, bot)
    await handlers.cleanup_history_handler(msg, bot)

    sent_texts = [args[1] for args, _kwargs in bot.messages]

    assert "stats report" in sent_texts
    assert "maintenance report" in sent_texts
    assert "errors cleanup" in sent_texts
    assert "history cleanup" in sent_texts

    # Slash commands must leave an audit trail, not just menu actions.
    assert audited == [
        (123, "cmd_stats"),
        (123, "cmd_maintenance"),
        (123, "cmd_cleanup_errors"),
        (123, "cmd_cleanup_history"),
    ]


@pytest.mark.asyncio
async def test_non_admin_slash_command_is_not_audited(monkeypatch):
    """A rejected caller must not produce an audit entry."""
    bot = AsyncFakeBot()
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: False)

    audited: list[tuple[int, str]] = []
    monkeypatch.setattr(
        handlers,
        "save_admin_audit",
        to_async(lambda admin_id, action: audited.append((admin_id, action))),
    )

    await handlers.stats_handler(fake_message(user_id=999), bot)

    assert audited == []


@pytest.mark.asyncio
async def test_admin_handlers_reject_non_admin(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: False)

    msg = fake_message(user_id=999)
    await handlers.stats_handler(msg, bot)
    await handlers.maintenance_handler(msg, bot)

    sent_texts = [args[1] for args, _kwargs in bot.messages]

    assert all("admin" in text.lower() or "only" in text.lower() for text in sent_texts)


# ── handle_admin_action (the bottom-menu admin dispatcher) ────────────────────
#
# Distinct code path from stats_handler/maintenance_handler/etc. above, which
# are the /slash-command entry points. handle_admin_action is what the admin
# bottom-menu buttons route through (text_handler -> handle_admin_action) and
# had zero test coverage before this — a typo in one of its six
# `if action == "..."` comparisons would have silently misrouted with nothing
# to catch it.


@pytest.mark.asyncio
async def test_handle_admin_action_routes_each_action_to_its_report(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: user_id == 123)
    monkeypatch.setattr(handlers, "format_stats_report", to_async(lambda language="en": "stats report"))
    monkeypatch.setattr(
        handlers, "format_maintenance_report", to_async(lambda language="en": "maintenance report")
    )
    monkeypatch.setattr(
        handlers, "cleanup_errors_report", to_async(lambda language="en": "errors cleanup")
    )
    monkeypatch.setattr(
        handlers, "cleanup_history_report", to_async(lambda language="en": "history cleanup")
    )
    monkeypatch.setattr(handlers, "format_health_report", to_async(lambda: "health report"))
    monkeypatch.setattr(handlers, "reload_admins_report", lambda language="en": "admins reloaded")
    monkeypatch.setattr(handlers, "save_admin_audit", to_async(lambda *a, **kw: None))

    msg = fake_message(user_id=123)

    action_to_expected_text = {
        "admin_stats": "stats report",
        "admin_maintenance": "maintenance report",
        "admin_cleanup_errors": "errors cleanup",
        "admin_cleanup_history": "history cleanup",
        "admin_health": "health report",
        "admin_reload_admins": "admins reloaded",
    }

    for action, expected_text in action_to_expected_text.items():
        bot.messages.clear()
        await handlers.handle_admin_action(bot, msg, action)
        assert bot.messages, f"no message sent for action={action!r}"
        assert bot.messages[-1][0][1] == expected_text, f"wrong report for action={action!r}"


@pytest.mark.asyncio
async def test_handle_admin_action_rejects_non_admin(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(handlers, "upsert_user", to_async(lambda user: None))
    monkeypatch.setattr(handlers, "get_user_language", to_async(lambda user_id: "en"))
    monkeypatch.setattr(handlers, "is_admin_user", lambda user_id: False)

    msg = fake_message(user_id=999)
    await handlers.handle_admin_action(bot, msg, "admin_maintenance")

    sent_texts = [args[1] for args, _kwargs in bot.messages]

    assert len(sent_texts) == 1
    assert "admin" in sent_texts[0].lower() or "only" in sent_texts[0].lower()
