import pytest

from app.config.settings import Settings, parse_bool, parse_optional_int


def make_valid_settings(**overrides):
    values = {
        "BOT_TOKEN": "test-token",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
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


def test_webhook_enabled_true_only_for_webhook_mode():
    assert make_valid_settings(BOT_MODE="polling").webhook_enabled is False
    assert make_valid_settings(BOT_MODE="webhook").webhook_enabled is True


def test_settings_validate_rejects_invalid_bot_mode():
    settings = make_valid_settings(BOT_MODE="carrier-pigeon")

    with pytest.raises(ValueError, match="BOT_MODE must be 'polling' or 'webhook'"):
        settings.validate()


def test_settings_validate_polling_mode_does_not_require_webhook_fields():
    """
    Never-break check: BOT_MODE=polling (the default) must validate cleanly
    with every WEBHOOK_* field left unset.
    """
    settings = make_valid_settings(BOT_MODE="polling")
    settings.validate()


def test_settings_validate_webhook_mode_requires_all_webhook_fields():
    settings = make_valid_settings(BOT_MODE="webhook")

    with pytest.raises(ValueError, match="BOT_MODE=webhook requires") as excinfo:
        settings.validate()

    for field in (
        "WEBHOOK_PUBLIC_URL",
        "WEBHOOK_SECRET_PATH",
        "WEBHOOK_SECRET_TOKEN",
        "WEBHOOK_CERT_PATH",
        "WEBHOOK_KEY_PATH",
    ):
        assert field in str(excinfo.value)


def test_settings_validate_webhook_mode_accepts_complete_config():
    make_valid_settings(
        BOT_MODE="webhook",
        WEBHOOK_PUBLIC_URL="https://example.com:8443",
        WEBHOOK_SECRET_PATH="secret-path",
        WEBHOOK_SECRET_TOKEN="secret-token",
        WEBHOOK_CERT_PATH="/certs/cert.pem",
        WEBHOOK_KEY_PATH="/certs/key.pem",
    ).validate()


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
        ("DATABASE_URL", None, "DATABASE_URL is not set"),
    ],
)
def test_settings_validate_rejects_invalid_config(field, value, message):
    settings = make_valid_settings(**{field: value})

    with pytest.raises(ValueError, match=message):
        settings.validate()
