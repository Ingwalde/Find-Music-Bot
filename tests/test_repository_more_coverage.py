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
