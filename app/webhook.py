import asyncio
import ssl

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config.settings import settings


def build_ssl_context() -> ssl.SSLContext:
    """
    Builds a server-side TLS context from the configured self-signed
    certificate and key. The app terminates TLS itself — no reverse proxy
    sits in front of it.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(settings.webhook_cert_path, settings.webhook_key_path)
    return context


def create_webhook_app(bot: Bot, dispatcher: Dispatcher) -> web.Application:
    """
    Builds the aiohttp application that receives Telegram webhook updates.

    SimpleRequestHandler validates the X-Telegram-Bot-Api-Secret-Token header
    against secret_token on every request and rejects mismatches before the
    update reaches the dispatcher — this is aiogram's own check, not
    hand-rolled here.
    """
    app = web.Application()

    handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET_TOKEN,
    )
    handler.register(app, path=f"/{settings.WEBHOOK_SECRET_PATH}")
    setup_application(app, dispatcher, bot=bot)

    return app


async def run_webhook_server(bot: Bot, dispatcher: Dispatcher) -> None:
    """
    Serves the webhook app with TLS until cancelled.

    Uses aiohttp's AppRunner/TCPSite directly instead of aiogram's own
    web.run_app helper, because web.run_app blocks and owns the event loop —
    this needs to run as one task alongside the polling/monitoring tasks in
    app.main.run_bot(), not take over the process.
    """
    app = create_webhook_app(bot, dispatcher)
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        host="0.0.0.0",
        port=settings.WEBHOOK_PORT,
        ssl_context=build_ssl_context(),
    )
    await site.start()

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


def webhook_url() -> str:
    """
    Full URL Telegram POSTs updates to — WEBHOOK_PUBLIC_URL is the scheme
    plus reachable host and port (e.g. https://203.0.113.10:8443), and the
    secret path is appended so the path itself only appears once, here.
    """
    return f"{settings.WEBHOOK_PUBLIC_URL}/{settings.WEBHOOK_SECRET_PATH}"
