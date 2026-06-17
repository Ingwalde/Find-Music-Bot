from types import SimpleNamespace

import pytest

from app.bot import similar_callbacks
from tests.conftest import AsyncFakeBot, to_async


def fake_call(track_id="123", user_id=42):
    return SimpleNamespace(
        id="call-id",
        data=f"similar:{track_id}",
        from_user=SimpleNamespace(id=user_id, username="tester", first_name="Test"),
        message=SimpleNamespace(chat=SimpleNamespace(id=10), message_id=20),
    )


def make_track(title="SOS", artist="ABBA"):
    return {
        "deezer_track_id": "1",
        "title": title,
        "artist": artist,
        "deezer_link": "https://deezer.com/track/1",
    }


@pytest.mark.asyncio
async def test_handle_similar_callback_sends_tracks_list(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(similar_callbacks, "get_user_language", to_async(lambda uid: "en"))
    monkeypatch.setattr(similar_callbacks, "get_track", to_async(lambda tid: make_track()))
    monkeypatch.setattr(
        similar_callbacks,
        "get_similar_by_genre",
        to_async(lambda tid, artist_name="": [make_track("Waterloo", "ABBA")]),
    )

    await similar_callbacks.handle_similar_callback(bot, fake_call("123"), "123")

    assert len(bot.answers) == 1
    assert len(bot.messages) == 1
    assert "ABBA" in bot.messages[0][0][1]


@pytest.mark.asyncio
async def test_handle_similar_callback_sends_empty_message_when_no_tracks(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(similar_callbacks, "get_user_language", to_async(lambda uid: "en"))
    monkeypatch.setattr(similar_callbacks, "get_track", to_async(lambda tid: make_track()))
    monkeypatch.setattr(similar_callbacks, "get_similar_by_genre", to_async(lambda tid, artist_name="": []))

    await similar_callbacks.handle_similar_callback(bot, fake_call("123"), "123")

    assert len(bot.messages) == 1
    assert "No similar" in bot.messages[0][0][1]


@pytest.mark.asyncio
async def test_handle_similar_callback_uses_fallback_header_when_get_track_fails(monkeypatch):
    bot = AsyncFakeBot()

    async def failing_get_track(tid):
        raise RuntimeError("fail")

    monkeypatch.setattr(similar_callbacks, "get_user_language", to_async(lambda uid: "en"))
    monkeypatch.setattr(similar_callbacks, "get_track", failing_get_track)
    monkeypatch.setattr(similar_callbacks, "get_similar_by_genre", to_async(lambda tid, artist_name="": [make_track()]))

    await similar_callbacks.handle_similar_callback(bot, fake_call("123"), "123")

    assert len(bot.messages) == 1


@pytest.mark.asyncio
async def test_handle_similar_callback_handles_exception_gracefully(monkeypatch):
    bot = AsyncFakeBot()

    async def failing_get_similar(tid, artist_name=""):
        raise RuntimeError("network error")

    monkeypatch.setattr(similar_callbacks, "get_user_language", to_async(lambda uid: "en"))
    monkeypatch.setattr(similar_callbacks, "get_track", to_async(lambda tid: make_track()))
    monkeypatch.setattr(similar_callbacks, "get_similar_by_genre", failing_get_similar)
    monkeypatch.setattr(similar_callbacks, "log_and_save_error", to_async(lambda **kwargs: None))

    await similar_callbacks.handle_similar_callback(bot, fake_call("123"), "123")

    assert len(bot.messages) == 1
    assert "No similar" in bot.messages[0][0][1]


@pytest.mark.asyncio
async def test_handle_similar_callback_shows_up_to_five_tracks(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(similar_callbacks, "get_user_language", to_async(lambda uid: "en"))
    monkeypatch.setattr(similar_callbacks, "get_track", to_async(lambda tid: make_track()))
    many = [make_track(f"Track {i}", "ABBA") for i in range(10)]
    monkeypatch.setattr(similar_callbacks, "get_similar_by_genre", to_async(lambda tid, artist_name="": many))

    await similar_callbacks.handle_similar_callback(bot, fake_call("123"), "123")

    text = bot.messages[0][0][1]
    assert "Track 4" in text
    assert "Track 5" not in text
