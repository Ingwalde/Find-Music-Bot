from types import SimpleNamespace

from app.database import repositories as repo
from app.database.db import get_connection
from app.localization.languages import DEFAULT_LANGUAGE


def make_user(user_id=123, username="tester", first_name="Test"):
    return SimpleNamespace(id=user_id, username=username, first_name=first_name)


def test_user_lookup_and_language_defaults(temp_database):
    assert repo.get_user_id(999) is None
    assert repo.get_user_language(None) == DEFAULT_LANGUAGE
    assert repo.get_user_language(999) == DEFAULT_LANGUAGE


def test_set_user_language_falls_back_for_unsupported_language(temp_database):
    user = make_user()
    repo.upsert_user(user)

    repo.set_user_language(user.id, "unsupported")

    assert repo.get_user_language(user.id) == DEFAULT_LANGUAGE


def test_upsert_user_preserves_existing_language(temp_database):
    user = make_user()
    repo.upsert_user(user)
    repo.set_user_language(user.id, "uk")

    repo.upsert_user(make_user(username="new_username", first_name="New"))

    assert repo.get_user_language(user.id) == "uk"


def test_get_user_language_falls_back_when_database_value_is_invalid(temp_database):
    user = make_user()
    repo.upsert_user(user)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ? WHERE telegram_id = ?", ("xx", user.id))
    conn.commit()
    conn.close()

    assert repo.get_user_language(user.id) == DEFAULT_LANGUAGE


def test_save_search_ignores_missing_user_and_blank_query(temp_database):
    repo.save_search(999, "SOS")

    user = make_user()
    repo.upsert_user(user)
    repo.save_search(user.id, "   ")

    assert repo.get_search_history(user.id) == []


def test_get_search_query_by_id_checks_owner_and_missing_rows(temp_database):
    first_user = make_user(1, "first", "First")
    second_user = make_user(2, "second", "Second")
    repo.upsert_user(first_user)
    repo.upsert_user(second_user)

    repo.save_search(first_user.id, "ABBA SOS")
    search_id = repo.get_search_history(first_user.id, limit=1)[0]["id"]

    assert repo.get_search_query_by_id(first_user.id, search_id) == "ABBA SOS"
    assert repo.get_search_query_by_id(second_user.id, search_id) is None
    assert repo.get_search_query_by_id(first_user.id, 999999) is None


def test_clear_search_history_ignores_missing_user(temp_database):
    repo.clear_search_history(404)
    assert repo.get_search_history(404) == []


def test_save_and_get_last_track_id(temp_database):
    user = make_user()
    repo.upsert_user(user)

    repo.save_last_track_id(user.id, "99887766")
    result = repo.get_last_track_id(user.id)

    assert result == "99887766"


def test_get_last_track_id_returns_none_for_unknown_user(temp_database):
    assert repo.get_last_track_id(999999) is None


def test_get_last_track_id_returns_none_before_any_track_opened(temp_database):
    user = make_user()
    repo.upsert_user(user)

    assert repo.get_last_track_id(user.id) is None


def test_save_last_track_id_overwrites_previous_value(temp_database):
    user = make_user()
    repo.upsert_user(user)

    repo.save_last_track_id(user.id, "111")
    repo.save_last_track_id(user.id, "222")

    assert repo.get_last_track_id(user.id) == "222"


def test_get_tracks_by_artist_returns_matching_tracks(temp_database, sample_track):
    repo.save_track(sample_track)

    other = dict(sample_track)
    other["deezer_track_id"] = "999"
    other["title"] = "Another Track"
    repo.save_track(other)

    results = repo.get_tracks_by_artist(
        artist=sample_track["artist"],
        exclude_deezer_id="999",
        limit=5,
    )

    assert len(results) == 1
    assert results[0]["deezer_track_id"] == sample_track["deezer_track_id"]


def test_get_tracks_by_artist_excludes_given_track(temp_database, sample_track):
    repo.save_track(sample_track)

    results = repo.get_tracks_by_artist(
        artist=sample_track["artist"],
        exclude_deezer_id=sample_track["deezer_track_id"],
        limit=5,
    )

    assert results == []


def test_get_tracks_by_artist_returns_empty_for_unknown_artist(temp_database):
    results = repo.get_tracks_by_artist(
        artist="No Such Artist",
        exclude_deezer_id="0",
    )

    assert results == []
