from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.database.db import get_pool
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


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
        Readiness probe. Returns 200 if the database is reachable,
        503 otherwise. Accepts HEAD as well as GET, for consistency with
        /health.
        """
        if await _check_database_ready():
            return JSONResponse(status_code=200, content={"status": "ok"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})

    @app.get("/metrics")
    async def metrics() -> Response:
        """
        Prometheus metrics endpoint. Scraped by Prometheus or any compatible
        agent (Grafana Agent, VictoriaMetrics, etc.).
        """
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


__all__ = [
    "create_app",
]
