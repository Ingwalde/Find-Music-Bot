import pytest

from app.config.settings import Settings, parse_bool, parse_optional_int


def make_valid_settings(**overrides):
    values = {
        "BOT_TOKEN": "test-token",
        "MAX_SEARCH_RESULTS": 30,
        "RESULTS_PER_PAGE": 5,
        "HISTORY_LIMIT": 10,
        "MAX_HISTORY_PER_USER": 100,
        "LOG_LEVEL": "INFO",
        "ERROR_HISTORY_LIMIT": 10,
        "SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS": 3600,
    }
    values.update(overrides)
    return Settings(**values)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("123", 123),
        ("not-a-number", None),
    ],
)
def test_parse_optional_int(raw_value, expected):
    assert parse_optional_int(raw_value) == expected


@pytest.mark.parametrize(
    ("raw_value", "default", "expected"),
    [
        (None, True, True),
        (None, False, False),
        ("1", False, True),
        ("true", False, True),
        ("YES", False, True),
        ("on", False, True),
        ("0", True, False),
        ("false", True, False),
    ],
)
def test_parse_bool(raw_value, default, expected):
    assert parse_bool(raw_value, default=default) is expected


def test_spotify_enabled_requires_flag_and_credentials():
    assert make_valid_settings(
        SPOTIFY_ENABLED=True,
        SPOTIFY_CLIENT_ID="client",
        SPOTIFY_CLIENT_SECRET="secret",
    ).spotify_enabled is True

    assert make_valid_settings(
        SPOTIFY_ENABLED=False,
        SPOTIFY_CLIENT_ID="client",
        SPOTIFY_CLIENT_SECRET="secret",
    ).spotify_enabled is False

    assert make_valid_settings(
        SPOTIFY_ENABLED=True,
        SPOTIFY_CLIENT_ID=None,
        SPOTIFY_CLIENT_SECRET="secret",
    ).spotify_enabled is False


def test_settings_validate_accepts_valid_config():
    make_valid_settings().validate()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("BOT_TOKEN", None, "BOT_TOKEN is not set"),
        ("MAX_SEARCH_RESULTS", 0, "MAX_SEARCH_RESULTS must be greater than 0"),
        ("MAX_SEARCH_RESULTS", 51, "MAX_SEARCH_RESULTS should not be greater than 50"),
        ("RESULTS_PER_PAGE", 0, "RESULTS_PER_PAGE must be greater than 0"),
        ("RESULTS_PER_PAGE", 31, "RESULTS_PER_PAGE cannot be greater"),
        ("HISTORY_LIMIT", 0, "HISTORY_LIMIT must be greater than 0"),
        ("HISTORY_LIMIT", 31, "HISTORY_LIMIT should not be greater than 30"),
        ("MAX_HISTORY_PER_USER", 5, "MAX_HISTORY_PER_USER cannot be smaller"),
        ("LOG_LEVEL", "TRACE", "LOG_LEVEL must be one of"),
        ("ERROR_HISTORY_LIMIT", 0, "ERROR_HISTORY_LIMIT must be greater than 0"),
        ("ERROR_HISTORY_LIMIT", 51, "ERROR_HISTORY_LIMIT should not be greater than 50"),
        (
            "SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS",
            30,
            "SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS should be at least 60",
        ),
    ],
)
def test_settings_validate_rejects_invalid_config(field, value, message):
    settings = make_valid_settings(**{field: value})

    with pytest.raises(ValueError, match=message):
        settings.validate()
