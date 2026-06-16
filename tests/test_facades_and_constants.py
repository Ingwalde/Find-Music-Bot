from app import version
from app.database import spotify_repository
from app.localization.languages import DEFAULT_LANGUAGE, get_language_label, is_supported_language
from app.services import track_platform_service


def test_version_is_300():
    assert version.__version__ == "3.0.0"


def test_track_platform_service_facade_exports_expected_functions():
    assert callable(track_platform_service.enrich_track_with_platform_links)
    assert callable(track_platform_service.enrich_track_with_spotify_link)
    assert "enrich_track_with_platform_links" in track_platform_service.__all__


def test_spotify_repository_facade_exports_expected_functions():
    assert callable(spotify_repository.get_spotify_data_by_deezer_id)
    assert callable(spotify_repository.update_spotify_data_for_track)
    assert "get_spotify_data_by_deezer_id" in spotify_repository.__all__


def test_language_helpers():
    assert DEFAULT_LANGUAGE == "en"
    assert is_supported_language("uk") is True
    assert is_supported_language("unknown") is False
    assert get_language_label("no") == "🇳🇴 Norsk"
    assert get_language_label("unknown") == "🇬🇧 English"
