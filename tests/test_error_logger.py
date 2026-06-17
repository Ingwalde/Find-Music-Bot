import pytest

from app.utils import error_logger


class FakeLogger:
    def __init__(self):
        self.exceptions = []
        self.warnings = []

    def exception(self, message, *args):
        self.exceptions.append((message, args))

    def warning(self, message, *args):
        self.warnings.append((message, args))


def test_error_to_message_returns_exception_type_and_message():
    message = error_logger.error_to_message(ValueError("wrong value"))

    assert "ValueError" in message
    assert "wrong value" in message


@pytest.mark.asyncio
async def test_log_and_save_error_saves_short_error(monkeypatch):
    saved = {}
    logger = FakeLogger()

    async def fake_save_error(**kwargs):
        saved.update(kwargs)

    monkeypatch.setattr(error_logger, "save_error", fake_save_error)

    await error_logger.log_and_save_error(logger, 123, "unit_test", RuntimeError("boom"))

    assert logger.exceptions
    assert saved["telegram_id"] == 123
    assert saved["source"] == "unit_test"
    assert "RuntimeError" in saved["error_message"]
    assert "boom" in saved["error_message"]


@pytest.mark.asyncio
async def test_log_and_save_error_does_not_raise_when_database_logging_fails(monkeypatch):
    logger = FakeLogger()

    async def raise_save_error(**kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(error_logger, "save_error", raise_save_error)

    await error_logger.log_and_save_error(logger, None, "unit_test", RuntimeError("original"))

    assert logger.exceptions
    assert logger.warnings
    assert "Could not save error" in logger.warnings[0][0]
