import logging

import pytest

import app.utils.logger as logger_module
from app.config.settings import parse_ratio


def make_record(level: int, exc_info=None) -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=level,
        pathname=__file__,
        lineno=1,
        msg="message",
        args=(),
        exc_info=exc_info,
    )


@pytest.mark.parametrize(
    "level",
    [logging.WARNING, logging.ERROR, logging.CRITICAL],
)
def test_warning_and_above_is_never_sampled_out(level):
    """An error must never be silently dropped, whatever the rate."""
    sampler = logger_module._SamplingFilter(sample_rate=0.0)

    assert sampler.filter(make_record(level)) is True


def test_records_with_exception_info_are_always_kept():
    sampler = logger_module._SamplingFilter(sample_rate=0.0)

    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = make_record(logging.INFO, exc_info=sys.exc_info())

    assert sampler.filter(record) is True


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO])
def test_rate_zero_drops_debug_and_info(level):
    sampler = logger_module._SamplingFilter(sample_rate=0.0)

    assert sampler.filter(make_record(level)) is False


@pytest.mark.parametrize("level", [logging.DEBUG, logging.INFO])
def test_rate_one_keeps_debug_and_info(level):
    sampler = logger_module._SamplingFilter(sample_rate=1.0)

    assert sampler.filter(make_record(level)) is True


def test_partial_rate_keeps_roughly_that_fraction(monkeypatch):
    """Deterministic check — random() is stubbed rather than sampled."""
    sampler = logger_module._SamplingFilter(sample_rate=0.5)

    monkeypatch.setattr(logger_module.random, "random", lambda: 0.4)
    assert sampler.filter(make_record(logging.INFO)) is True

    monkeypatch.setattr(logger_module.random, "random", lambda: 0.6)
    assert sampler.filter(make_record(logging.INFO)) is False


def test_no_sampling_filter_attached_at_the_default_rate(monkeypatch):
    """Rate 1.0 must add no filter at all — zero overhead on the default path."""
    monkeypatch.setattr(logger_module.settings, "LOG_SAMPLE_RATE", 1.0)
    monkeypatch.setattr(logger_module, "_LOGGING_CONFIGURED", False)

    logger_module.setup_logging()

    for handler in logging.getLogger().handlers:
        assert not any(
            isinstance(f, logger_module._SamplingFilter) for f in handler.filters
        )


def test_sampling_filter_attached_to_every_handler_when_rate_is_lowered(monkeypatch):
    monkeypatch.setattr(logger_module.settings, "LOG_SAMPLE_RATE", 0.5)
    monkeypatch.setattr(logger_module, "_LOGGING_CONFIGURED", False)

    logger_module.setup_logging()

    handlers = logging.getLogger().handlers
    assert handlers
    for handler in handlers:
        assert any(isinstance(f, logger_module._SamplingFilter) for f in handler.filters)

    # Restore the default so later tests see an unsampled logger.
    monkeypatch.setattr(logger_module.settings, "LOG_SAMPLE_RATE", 1.0)
    monkeypatch.setattr(logger_module, "_LOGGING_CONFIGURED", False)
    logger_module.setup_logging()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 1.0),
        ("", 1.0),
        ("   ", 1.0),
        ("0.5", 0.5),
        ("0", 0.0),
        ("1", 1.0),
        ("not a number", 1.0),
        ("-0.5", 0.0),
        ("7", 1.0),
    ],
)
def test_parse_ratio_clamps_and_falls_back(raw, expected):
    assert parse_ratio(raw, default=1.0) == expected
