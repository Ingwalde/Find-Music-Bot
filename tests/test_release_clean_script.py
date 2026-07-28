import pytest

from scripts.check_release_clean import is_forbidden


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "certs/cert.pem",
        "certs/key.pem",
        "certs/nested/cert.pem",
        "data/music_bot.db",
        "logs/bot.log",
    ],
)
def test_is_forbidden_rejects_private_files(path):
    assert is_forbidden(path) is True


@pytest.mark.parametrize(
    "path",
    [
        ".env.example",
        "config/admins.example.json",
        "app/config/settings.py",
        "docs/DEPLOYMENT.md",
    ],
)
def test_is_forbidden_allows_tracked_files(path):
    assert is_forbidden(path) is False


def test_is_forbidden_handles_windows_path_separators():
    assert is_forbidden("certs\\key.pem") is True
