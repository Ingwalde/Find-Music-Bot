import json
import logging
import traceback
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config.settings import settings

_LOGGING_CONFIGURED = False


class _JsonFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects for structured log ingestion
    (Loki, ELK, CloudWatch, etc.). Includes correlation_id when set by the
    CorrelationIdFilter injected at setup time.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlation_id"] = correlation_id

        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(payload, ensure_ascii=False)


class _CorrelationIdFilter(logging.Filter):
    """
    Injects the current correlation_id (set per Telegram update by the
    CorrelationMiddleware) into every log record. When no update is active
    the field is absent from the JSON output.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        from app.utils.correlation import get_correlation_id

        cid = get_correlation_id()
        if cid:
            record.correlation_id = cid
        return True


def setup_logging() -> None:
    """
    Configures application logging once.

    Logs are written to console and LOG_FILE_PATH.
    Set LOG_FORMAT=json for structured JSON output (default: plain text).
    """
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    if settings.LOG_FORMAT == "json":
        formatter: logging.Formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    correlation_filter = _CorrelationIdFilter()

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)

    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)
    root_logger.addHandler(file_handler)

    _LOGGING_CONFIGURED = True


def setup_logger(name: str) -> logging.Logger:
    """
    Returns project logger and ensures logging is configured.
    """
    setup_logging()
    return logging.getLogger(name)
