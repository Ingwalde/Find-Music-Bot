import re
from pathlib import Path

from app import version
from app.database import spotify_repository
from app.localization.languages import DEFAULT_LANGUAGE, get_language_label, is_supported_language
from app.services import track_platform_service


def test_version_is_semver():
    """
    Deliberately not pinned to a literal. The previous form asserted
    == "3.7.0", so every release had to edit this test — and once it stopped
    being edited, version.py silently sat at 3.7.0 from v3.7.1 through v3.7.7
    while /version and the admin /maintenance report showed the stale value.
    Agreement with CHANGELOG.md is enforced below and by check_version_sync.py.
    """
    assert re.fullmatch(r"\d+\.\d+\.\d+", version.__version__)


def test_version_matches_the_newest_changelog_entry():
    changelog = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
    match = re.search(r"^##\s*\[v(\d+\.\d+\.\d+)\]", changelog.read_text(encoding="utf-8"), re.M)

    assert match, "CHANGELOG.md has no '## [vX.Y.Z]' heading"
    assert version.__version__ == match.group(1)


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
