import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config.settings import settings

_LOGGING_CONFIGURED = False


def setup_logging() -> None:
    """
    Configures application logging once.

    Logs are written to:
    - console
    - file from LOG_FILE_PATH, for example logs/bot.log
    """
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers after imports/restarts in development.
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _LOGGING_CONFIGURED = True


def setup_logger(name: str) -> logging.Logger:
    """
    Returns project logger and ensures logging is configured.
    """
    setup_logging()
    return logging.getLogger(name)
