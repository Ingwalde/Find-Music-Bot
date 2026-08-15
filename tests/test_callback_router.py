import pytest

from app.bot import callbacks
from tests.conftest import AsyncFakeBot, fake_call, to_async


@pytest.mark.asyncio
async def test_callback_router_handles_page_data_missing_separator(monkeypatch):
    """
    CB_PAGE with no ":" suffix — data.split(":", 1)[1] would raise IndexError
    before this guard existed. Must answer unknown_action, not raise.
    """
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))
    bot = AsyncFakeBot()
    call = fake_call(data=callbacks.CB_PAGE)

    await callbacks.callback_router(call, bot)

    assert len(bot.answers) == 1
    args, kwargs = bot.answers[0]
    assert kwargs.get("show_alert") is False


@pytest.mark.asyncio
async def test_callback_router_handles_non_numeric_page_value(monkeypatch):
    """
    CB_PAGE with a non-numeric suffix — int(...) would raise ValueError
    before this guard existed. Must answer unknown_action, not raise.
    """
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))
    bot = AsyncFakeBot()
    call = fake_call(data=f"{callbacks.CB_PAGE}:not-a-number")

    await callbacks.callback_router(call, bot)

    assert len(bot.answers) == 1


@pytest.mark.asyncio
async def test_callback_router_handles_prefix_with_no_separator(monkeypatch):
    """
    Any other CB_* prefix matched exactly with no ":" suffix hits the same
    IndexError guard (not just CB_PAGE's extra int() parse).
    """
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))
    bot = AsyncFakeBot()
    call = fake_call(data=callbacks.CB_TRACK)

    await callbacks.callback_router(call, bot)

    assert len(bot.answers) == 1


@pytest.mark.asyncio
async def test_callback_router_still_dispatches_valid_page_data(monkeypatch):
    """
    Regression guard: the try/except wrapping must not change behavior for
    well-formed callback_data.
    """
    monkeypatch.setattr(callbacks, "get_user_language", to_async(lambda user_id: "en"))

    called_with = {}

    async def fake_handle_page_callback(bot, call, page, language):
        called_with["page"] = page

    monkeypatch.setattr(callbacks, "handle_page_callback", fake_handle_page_callback)

    bot = AsyncFakeBot()
    call = fake_call(data=f"{callbacks.CB_PAGE}:2")

    await callbacks.callback_router(call, bot)

    assert called_with["page"] == 2
