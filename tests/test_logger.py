import logging
from logging.handlers import TimedRotatingFileHandler

import app.utils.logger as logger_module


def test_file_handler_is_timed_rotating_daily_keeping_5_backups(monkeypatch):
    """
    Forces a fresh setup_logging() call regardless of prior state.

    setup_logging()'s own _LOGGING_CONFIGURED guard makes a plain re-call
    a no-op once already True — but other libraries used elsewhere in the
    suite (e.g. asyncpg/the compose test-postgres service, used by the live_pg fixture) can
    reconfigure the root logger's handlers as their own side effect,
    bypassing this module's guard entirely since they never call
    setup_logging(). Resetting the guard here forces a real
    reconfiguration so this assertion doesn't depend on suite-wide test
    order or third-party side effects.
    """
    monkeypatch.setattr(logger_module, "_LOGGING_CONFIGURED", False)
    logger_module.setup_logging()

    root_logger = logging.getLogger()
    file_handlers = [
        handler for handler in root_logger.handlers if isinstance(handler, TimedRotatingFileHandler)
    ]

    assert len(file_handlers) == 1

    handler = file_handlers[0]
    assert handler.when == "MIDNIGHT"
    assert handler.backupCount == 5
