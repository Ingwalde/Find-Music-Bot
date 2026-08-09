import httpx

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

_DEFAULT_TIMEOUT = 10.0
_client: httpx.AsyncClient | None = None


async def init_http_client() -> None:
    global _client
    _client = httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
    logger.info("HTTP client initialized.")


async def close_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("HTTP client closed.")


def get_http_client() -> httpx.AsyncClient:
    """Returns the shared AsyncClient. Falls back to a new client when called
    outside the bot lifecycle (tests, scripts)."""
    return _client if _client is not None else httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
