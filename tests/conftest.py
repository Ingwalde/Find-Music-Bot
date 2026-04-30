import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def fake_user():
    """
    Returns a lightweight object compatible with repositories.upsert_user().
    """
    return SimpleNamespace(
        id=123456789,
        username="test_user",
        first_name="Test",
    )


@pytest.fixture
def sample_track():
    """
    Returns normalized track dictionary used by database and formatter tests.
    """
    return {
        "deezer_track_id": "671298",
        "title": "Music & Me",
        "artist": "Nate Dogg",
        "album": "Music and Me",
        "duration": "04:00",
        "duration_seconds": 240,
        "deezer_link": "https://www.deezer.com/track/671298",
        "cover_url": "https://e-cdns-images.dzcdn.net/images/cover/test.jpg",
        "release_date": "2001-12-04",
        "rank": 789123,
        "popularity": "Very high",
    }


@pytest.fixture
def temp_database(tmp_path, monkeypatch):
    """
    Configures the app to use an isolated SQLite database for each test.
    """
    from app.config.settings import settings
    from app.database.db import init_db

    db_path = tmp_path / "test_music_bot.db"

    monkeypatch.setattr(settings, "DATABASE_PATH", str(db_path))
    monkeypatch.setattr(settings, "MAX_HISTORY_PER_USER", 5)
    monkeypatch.setattr(settings, "HISTORY_LIMIT", 3)

    init_db()

    return db_path


@pytest.fixture(autouse=True)
def clear_search_contexts():
    """
    Clears in-memory pagination/search contexts between tests.
    """
    from app.bot.context import search_contexts

    search_contexts.clear()
    yield
    search_contexts.clear()
