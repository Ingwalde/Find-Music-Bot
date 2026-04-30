from app.database import repositories as repo
from app.database.db import get_connection


def test_upsert_user_and_get_user_id(temp_database, fake_user):
    repo.upsert_user(fake_user)

    assert repo.get_user_id(fake_user.id) is not None


def test_save_search_and_unique_history_with_duplicates(temp_database, fake_user):
    repo.upsert_user(fake_user)

    repo.save_search(fake_user.id, "American Pie")
    repo.save_search(fake_user.id, "music")
    repo.save_search(fake_user.id, "american pie")

    history = repo.get_search_history(fake_user.id, limit=10)
    queries = [item["query"] for item in history]

    assert queries[0] == "american pie"
    assert "music" in queries
    assert len(queries) == 2


def test_search_history_is_trimmed(temp_database, fake_user, monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "MAX_HISTORY_PER_USER", 5)

    repo.upsert_user(fake_user)

    for index in range(10):
        repo.save_search(fake_user.id, f"query {index}")

    user_id = repo.get_user_id(fake_user.id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM searches WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    assert row["count"] == 5


def test_clear_search_history(temp_database, fake_user):
    repo.upsert_user(fake_user)
    repo.save_search(fake_user.id, "American Pie")

    repo.clear_search_history(fake_user.id)

    assert repo.get_search_history(fake_user.id) == []


def test_save_track_and_get_cached_track(temp_database, sample_track):
    track_id = repo.save_track(sample_track)

    cached_track = repo.get_track_by_deezer_id(sample_track["deezer_track_id"])

    assert track_id > 0
    assert cached_track["title"] == "Music & Me"
    assert cached_track["artist"] == "Nate Dogg"
    assert cached_track["rank"] == 789123
    assert "updated_at" in cached_track


def test_favorite_lifecycle(temp_database, fake_user, sample_track):
    repo.upsert_user(fake_user)

    assert repo.is_track_favorite(fake_user.id, sample_track["deezer_track_id"]) is False

    repo.add_favorite(fake_user.id, sample_track)

    assert repo.is_track_favorite(fake_user.id, sample_track["deezer_track_id"]) is True

    favorites = repo.get_favorite_tracks(fake_user.id)

    assert len(favorites) == 1
    assert favorites[0]["title"] == "Music & Me"

    repo.remove_favorite(fake_user.id, sample_track["deezer_track_id"])

    assert repo.is_track_favorite(fake_user.id, sample_track["deezer_track_id"]) is False


def test_clear_favorites(temp_database, fake_user, sample_track):
    repo.upsert_user(fake_user)
    repo.add_favorite(fake_user.id, sample_track)

    repo.clear_favorites(fake_user.id)

    assert repo.get_favorite_tracks(fake_user.id) == []


def test_error_lifecycle(temp_database):
    repo.save_error(telegram_id=123, source="unit_test", error_message="Something failed")

    errors = repo.get_recent_errors(limit=5)

    assert len(errors) == 1
    assert errors[0]["source"] == "unit_test"

    repo.clear_errors()

    assert repo.get_recent_errors(limit=5) == []


def test_database_indexes_are_created(temp_database):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
        """
    )
    index_names = {row["name"] for row in cursor.fetchall()}
    conn.close()

    assert "idx_users_telegram_id" in index_names
    assert "idx_tracks_deezer_track_id" in index_names
    assert "idx_searches_user_id" in index_names
