import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from app.config.settings import settings
from app.database.db import get_pool
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_tls_cert_expiry_days = Gauge(
    "bot_tls_cert_expiry_days",
    "Days until the TLS certificate expires (webhook mode only; -1 when unreadable)",
)


def _update_cert_expiry_metric() -> None:
    """Reads WEBHOOK_CERT_PATH and updates the expiry gauge. No-op when not in webhook mode."""
    cert_path = settings.WEBHOOK_CERT_PATH
    if not cert_path:
        return
    try:
        from cryptography import x509

        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        expiry = cert.not_valid_after_utc
        now = datetime.datetime.now(datetime.UTC)
        days = (expiry - now).total_seconds() / 86400
        _tls_cert_expiry_days.set(days)
    except Exception as exc:
        logger.warning("Could not read TLS cert expiry from %s: %s", cert_path, exc)
        _tls_cert_expiry_days.set(-1)


async def _check_database_ready() -> bool:
    """
    Checks whether the PostgreSQL database is reachable via the asyncpg pool.

    This is a distinct, HTTP-facing readiness check — separate from
    app.health.check_database(), which serves the Telegram-admin /health
    command.
    """
    try:
        async with (await get_pool()).acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as error:
        logger.warning("Readiness check failed: database unavailable: %s", error)
        return False


async def _check_redis_ready() -> bool:
    """
    Checks Redis connectivity for the /ready probe.
    Returns True when Redis is not configured (in-memory fallback is fine).
    """
    if not settings.REDIS_URL:
        return True

    from app.services.redis_client import get_redis_client

    client = get_redis_client()
    if client is None:
        logger.warning("Readiness check failed: Redis client not initialised")
        return False

    try:
        await client.ping()
        return True
    except Exception as error:
        logger.warning("Readiness check failed: Redis unavailable: %s", error)
        return False


def create_app() -> FastAPI:
    """
    Creates the FastAPI app exposing liveness and readiness probes.

    This factory only builds the app object and its routes — starting an
    HTTP server (uvicorn) is the responsibility of the integration stage
    that wires this into the bot's startup.
    """
    app = FastAPI(title="Find Music Bot Monitoring")

    @app.api_route("/health", methods=["GET", "HEAD"])
    async def health() -> dict[str, str]:
        """
        Liveness probe. Always returns 200 with no external calls.

        Accepts HEAD as well as GET — some uptime monitors (e.g. UptimeRobot's
        free tier) only send HEAD requests. Starlette strips the body for HEAD
        responses automatically; no extra handling needed here.
        """
        return {"status": "ok"}

    @app.api_route("/ready", methods=["GET", "HEAD"])
    async def ready() -> JSONResponse:
        """
        Readiness probe. Returns 200 if the database (and Redis, when configured)
        are reachable. Returns 503 otherwise. Accepts HEAD as well as GET.
        """
        db_ok = await _check_database_ready()
        redis_ok = await _check_redis_ready()
        if db_ok and redis_ok:
            return JSONResponse(status_code=200, content={"status": "ok"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})

    @app.get("/metrics")
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint. Scraped by Prometheus or any compatible
        agent (Grafana Agent, VictoriaMetrics, etc.).
        Updates the TLS cert expiry gauge on each scrape.
        """
        _update_cert_expiry_metric()
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


__all__ = [
    "create_app",
]
