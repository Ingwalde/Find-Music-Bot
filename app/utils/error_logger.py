import logging
from traceback import format_exception_only

from app.database.repositories import save_error


def error_to_message(error: Exception) -> str:
    """
    Converts exception to a short readable message for database storage.
    """
    message = "".join(
        format_exception_only(type(error), error)
    ).strip()

    return message or str(error)


def log_and_save_error(
    logger: logging.Logger,
    telegram_id: int | None,
    source: str,
    error: Exception,
) -> None:
    """
    Logs exception to console/file and saves short error info to SQLite.

    Database write errors are logged but not raised, so the bot does not crash
    while trying to log another error.
    """
    logger.exception("%s error: %s", source, error)

    try:
        save_error(
            telegram_id=telegram_id,
            source=source,
            error_message=error_to_message(error),
        )
    except Exception as logging_error:
        logger.warning("Could not save error to database: %s", logging_error)
