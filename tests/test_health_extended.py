from app import health
from app.health import HealthItem


def test_check_database_success(temp_database):
    item = health.check_database()

    assert item.name == "Database"
    assert item.ok is True
    assert "OK" in item.message


def test_check_database_failure(monkeypatch):
    def raise_database_error():
        raise RuntimeError("database is locked")

    monkeypatch.setattr(health, "get_connection", raise_database_error)

    item = health.check_database()

    assert item.name == "Database"
    assert item.ok is False
    assert "database is locked" in item.message


def test_check_spotify_disabled(monkeypatch):
    monkeypatch.setattr(health.settings, "SPOTIFY_ENABLED", False)

    item = health.check_spotify()

    assert item.ok is True
    assert item.message == "Disabled by configuration"


def test_check_spotify_without_credentials(monkeypatch):
    monkeypatch.setattr(health.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(health, "is_spotify_configured", lambda: False)

    item = health.check_spotify()

    assert item.ok is True
    assert "Optional credentials" in item.message


def test_check_spotify_temporarily_blocked(monkeypatch):
    monkeypatch.setattr(health.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(health, "is_spotify_configured", lambda: True)
    monkeypatch.setattr(health, "is_spotify_temporarily_blocked", lambda: True)
    monkeypatch.setattr(health, "get_spotify_block_reason", lambda: "403 Forbidden")

    item = health.check_spotify()

    assert item.ok is False
    assert "403 Forbidden" in item.message


def test_check_spotify_configured(monkeypatch):
    monkeypatch.setattr(health.settings, "SPOTIFY_ENABLED", True)
    monkeypatch.setattr(health, "is_spotify_configured", lambda: True)
    monkeypatch.setattr(health, "is_spotify_temporarily_blocked", lambda: False)

    item = health.check_spotify()

    assert item.ok is True
    assert item.message == "Configured"


def test_check_genius_configured(monkeypatch):
    monkeypatch.setattr(health.settings, "GENIUS_TOKEN", "token")

    item = health.check_genius()

    assert item.ok is True
    assert item.message == "Configured"


def test_check_genius_not_configured(monkeypatch):
    monkeypatch.setattr(health.settings, "GENIUS_TOKEN", None)

    item = health.check_genius()

    assert item.ok is True
    assert "Optional token" in item.message


def test_get_health_items_uses_all_checks(monkeypatch):
    monkeypatch.setattr(health, "check_database", lambda: HealthItem("Database", True, "OK"))
    monkeypatch.setattr(health, "check_deezer", lambda: HealthItem("Deezer", True, "OK"))
    monkeypatch.setattr(health, "check_spotify", lambda: HealthItem("Spotify", True, "OK"))
    monkeypatch.setattr(health, "check_genius", lambda: HealthItem("Genius", True, "OK"))

    item_names = [item.name for item in health.get_health_items()]

    assert item_names == ["Bot", "Database", "Deezer", "Spotify", "Genius"]
