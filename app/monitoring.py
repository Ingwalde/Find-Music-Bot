from fastapi import FastAPI
from fastapi.responses import JSONResponse

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

    @app.get("/health")
    async def health() -> dict[str, str]:
        """
        Liveness probe. Always returns 200 with no external calls.
        """
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> JSONResponse:
        """
        Readiness probe. Returns 200 if the database is reachable,
        503 otherwise.
        """
        if await _check_database_ready():
            return JSONResponse(status_code=200, content={"status": "ok"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})

    return app


__all__ = [
    "create_app",
]
