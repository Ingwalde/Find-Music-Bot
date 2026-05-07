def test_repository_facade_imports():
    from app.database.repositories import get_user_language, save_track, save_search

    assert callable(get_user_language)
    assert callable(save_track)
    assert callable(save_search)


def test_spotify_service_facade_imports():
    from app.services.spotify_service import (
        build_spotify_queries,
        format_spotify_track,
        normalize_text,
        search_spotify_track,
    )

    assert callable(build_spotify_queries)
    assert callable(format_spotify_track)
    assert callable(normalize_text)
    assert callable(search_spotify_track)


def test_translation_facade_imports():
    from app.localization.translations import get_menu_action_by_text, t

    assert t("btn_music", "en") == "🎵 Music"
    assert get_menu_action_by_text("🎵 Music") == "music"


def test_database_modules_imports():
    from app.database.indexes import create_indexes
    from app.database.migrations import migrate_db
    from app.database.schema import create_tables

    assert callable(create_tables)
    assert callable(migrate_db)
    assert callable(create_indexes)
