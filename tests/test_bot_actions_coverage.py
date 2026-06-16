import pytest

from app.bot import actions
from app.bot.context import save_search_context
from tests.conftest import AsyncFakeBot, to_async


@pytest.mark.asyncio
async def test_show_main_menu_uses_user_language(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "uk")

    await actions.show_main_menu(bot, chat_id=10, user_id=123)

    assert bot.messages
    assert bot.messages[0][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_ask_for_music_sends_prompt(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")

    await actions.ask_for_music(bot, chat_id=10, user_id=123)

    assert len(bot.messages) == 1
    assert bot.messages[0][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_search_results_rejects_empty_query(monkeypatch):
    bot = AsyncFakeBot()
    called = {"ask": False}
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(
        actions, "ask_for_music", to_async(lambda *args, **kwargs: called.update(ask=True))
    )

    await actions.send_search_results(bot, chat_id=10, user_id=123, query="   ")

    assert bot.messages
    assert called["ask"] is True


@pytest.mark.asyncio
async def test_send_search_results_handles_no_results(monkeypatch):
    bot = AsyncFakeBot()
    called = {"saved": False, "ask": False}
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "save_search", lambda user_id, query: called.update(saved=True))
    monkeypatch.setattr(actions, "search_tracks", to_async(lambda query, limit: []))
    monkeypatch.setattr(
        actions, "ask_for_music", to_async(lambda *args, **kwargs: called.update(ask=True))
    )

    await actions.send_search_results(bot, chat_id=10, user_id=123, query="SOS")

    assert called == {"saved": True, "ask": True}
    assert bot.messages


@pytest.mark.asyncio
async def test_send_search_results_saves_context_and_sends_keyboard(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    tracks = [sample_track | {"deezer_track_id": str(index), "title": f"Track {index}"} for index in range(3)]

    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "save_search", lambda user_id, query: None)
    monkeypatch.setattr(actions, "search_tracks", to_async(lambda query, limit: tracks))

    await actions.send_search_results(bot, chat_id=10, user_id=123, query="SOS")

    context = await actions.get_search_context(123)
    assert context["query"] == "SOS"
    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_current_results_page_handles_missing_context(monkeypatch):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")

    await actions.send_current_results_page(bot, chat_id=10, user_id=123)

    assert bot.messages


@pytest.mark.asyncio
async def test_send_current_results_page_sends_saved_context(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    await save_search_context(123, "SOS", [sample_track])

    await actions.send_current_results_page(bot, chat_id=10, user_id=123)

    assert bot.messages[-1][1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_send_track_card_sends_photo_when_cover_is_available(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: False)
    monkeypatch.setattr(actions, "user_has_search_context", to_async(lambda user_id: False))
    monkeypatch.setattr(actions, "get_db_recommendations", to_async(lambda **kwargs: []))

    await actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert bot.photos
    assert not bot.messages


@pytest.mark.asyncio
async def test_send_track_card_falls_back_to_message_when_photo_fails(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    bot.raise_on_photo = True
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: True)
    monkeypatch.setattr(actions, "user_has_search_context", to_async(lambda user_id: True))
    monkeypatch.setattr(actions, "get_db_recommendations", to_async(lambda **kwargs: []))

    await actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert bot.messages[-1][1]["text"] == "formatted"


@pytest.mark.asyncio
async def test_send_track_card_handles_last_track_id_error(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: False)
    monkeypatch.setattr(actions, "user_has_search_context", to_async(lambda user_id: False))
    monkeypatch.setattr(actions, "get_db_recommendations", to_async(lambda **kwargs: []))
    monkeypatch.setattr(
        actions,
        "save_last_track_id",
        lambda telegram_id, deezer_id: (_ for _ in ()).throw(RuntimeError("db error")),
    )
    monkeypatch.setattr(actions, "log_and_save_error", lambda *a, **k: calls.append(1))

    await actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert calls
    assert bot.photos


@pytest.mark.asyncio
async def test_send_track_card_sends_recommendations_when_available(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: False)
    monkeypatch.setattr(actions, "user_has_search_context", to_async(lambda user_id: False))
    monkeypatch.setattr(actions, "save_last_track_id", lambda telegram_id, deezer_id: None)
    monkeypatch.setattr(
        actions, "get_db_recommendations", to_async(lambda **kwargs: [sample_track])
    )
    monkeypatch.setattr(
        actions, "format_recommendations_text", lambda recs, source_artist: "rec text"
    )

    await actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert "rec text" in bot.messages[-1][1]["text"]


@pytest.mark.asyncio
async def test_send_track_card_handles_recommendations_error(monkeypatch, sample_track):
    bot = AsyncFakeBot()
    calls = []
    monkeypatch.setattr(actions, "get_user_language", lambda user_id: "en")
    monkeypatch.setattr(actions, "enrich_track_with_spotify_link", lambda track: track)
    monkeypatch.setattr(actions, "format_track_card", lambda track: "formatted")
    monkeypatch.setattr(actions, "is_track_favorite", lambda **kwargs: False)
    monkeypatch.setattr(actions, "user_has_search_context", to_async(lambda user_id: False))
    monkeypatch.setattr(actions, "save_last_track_id", lambda telegram_id, deezer_id: None)
    monkeypatch.setattr(
        actions,
        "get_db_recommendations",
        to_async(lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db error"))),
    )
    monkeypatch.setattr(actions, "log_and_save_error", lambda *a, **k: calls.append(1))

    await actions.send_track_card(bot, chat_id=10, telegram_id=123, track=sample_track)

    assert calls
