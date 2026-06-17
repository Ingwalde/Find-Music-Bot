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
