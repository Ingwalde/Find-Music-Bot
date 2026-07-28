import pytest
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.config.settings import settings
from app.webhook import build_ssl_context, create_webhook_app, webhook_url


@pytest.fixture
def bot():
    return Bot(token="12345:test-token")


@pytest.fixture
def dispatcher():
    return Dispatcher()


@pytest.fixture(autouse=True)
def webhook_settings(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_SECRET_TOKEN", "correct-token")
    monkeypatch.setattr(settings, "WEBHOOK_SECRET_PATH", "hook-path")


@pytest.mark.asyncio
async def test_create_webhook_app_rejects_missing_secret_token(bot, dispatcher):
    app = create_webhook_app(bot, dispatcher)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.post("/hook-path", json={"update_id": 1})
        assert resp.status == 401
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_create_webhook_app_rejects_wrong_secret_token(bot, dispatcher):
    app = create_webhook_app(bot, dispatcher)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.post(
            "/hook-path",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-token"},
        )
        assert resp.status == 401
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_create_webhook_app_accepts_correct_secret_token_at_secret_path(bot, dispatcher):
    app = create_webhook_app(bot, dispatcher)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        resp = await client.post(
            "/hook-path",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "correct-token"},
        )
        assert resp.status == 200
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_webhook_handler_feeds_parsed_update_to_dispatcher(bot, dispatcher):
    """
    Exercises the same SimpleRequestHandler/setup_application wiring
    create_webhook_app uses, with handle_in_background=False so the
    dispatcher call is synchronous and deterministic to assert on (the
    default background mode responds 200 before the update is processed).
    """
    received = {}

    async def fake_feed_webhook_update(bot_arg, update, **kwargs):
        received["bot"] = bot_arg
        received["update"] = update
        return None

    monkeypatch_target = dispatcher
    monkeypatch_target.feed_webhook_update = fake_feed_webhook_update

    app = web.Application()
    handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        handle_in_background=False,
        secret_token=settings.WEBHOOK_SECRET_TOKEN,
    )
    handler.register(app, path=f"/{settings.WEBHOOK_SECRET_PATH}")
    setup_application(app, dispatcher, bot=bot)

    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        payload = {
            "update_id": 42,
            "message": {
                "message_id": 1,
                "date": 0,
                "chat": {"id": 10, "type": "private"},
                "text": "hi",
            },
        }
        resp = await client.post(
            "/hook-path",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "correct-token"},
        )

        assert resp.status == 200
        assert received["bot"] is bot
        assert received["update"] == payload
    finally:
        await client.close()


def test_build_ssl_context_raises_for_missing_cert_files(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_CERT_PATH", "does/not/exist-cert.pem")
    monkeypatch.setattr(settings, "WEBHOOK_KEY_PATH", "does/not/exist-key.pem")

    with pytest.raises(FileNotFoundError):
        build_ssl_context()


def test_webhook_url_joins_public_url_and_secret_path(monkeypatch):
    monkeypatch.setattr(settings, "WEBHOOK_PUBLIC_URL", "https://example.com:8443")

    assert webhook_url() == "https://example.com:8443/hook-path"
