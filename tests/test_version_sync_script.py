"""
Covers the documentation half of scripts/check_version_sync.py.

The version half compares two files to each other, so it is satisfied as soon
as they match and cannot see work stacked above the newest CHANGELOG entry.
These tests drive the git-backed half against a real throwaway repository --
the behaviour is entirely about tags and commit ranges, so faking git would
test the fake.
"""

import shutil
import subprocess

import pytest

from scripts import check_version_sync

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def run_git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def write(repo, relative_path, text):
    path = repo / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def commit(repo, message, files):
    """`files` maps a repo-relative path to its content."""
    for relative_path, text in files.items():
        write(repo, relative_path, text)
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", message)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A repository at v1.0.0 with one commit, matching the real layout."""
    run_git(tmp_path, "init", "-q", "-b", "main")
    commit(
        tmp_path,
        "release v1.0.0",
        {
            "app/version.py": '__version__ = "1.0.0"\n',
            "CHANGELOG.md": "## [v1.0.0] - 2026-01-01\n",
        },
    )
    run_git(tmp_path, "tag", "v1.0.0")

    monkeypatch.setattr(check_version_sync, "PROJECT_ROOT", tmp_path)
    return tmp_path


def test_clean_release_passes(repo):
    assert check_version_sync.check_release_is_documented("1.0.0") == 0


def test_app_changes_without_a_changelog_entry_fail(repo, capsys):
    """The exact shape that let two undocumented changes reach main."""
    commit(repo, "refactor handlers", {"app/bot/handlers/menu.py": "x = 1\n"})

    assert check_version_sync.check_release_is_documented("1.0.0") == 1

    output = capsys.readouterr().out
    assert "app/ has changed since v1.0.0" in output
    assert "app/bot/handlers/menu.py" in output, "the offending files must be named"


def test_app_changes_with_a_changelog_entry_pass(repo):
    commit(
        repo,
        "feat with docs",
        {
            "app/services/thing.py": "x = 1\n",
            "CHANGELOG.md": "## [v1.1.0] - 2026-01-02\n\n## [v1.0.0] - 2026-01-01\n",
        },
    )

    assert check_version_sync.check_release_is_documented("1.0.0") == 0


def test_changelog_touched_in_a_separate_commit_still_passes(repo):
    """Documenting in a follow-up commit is fine; the range is what matters."""
    commit(repo, "code", {"app/services/thing.py": "x = 1\n"})
    commit(repo, "docs", {"CHANGELOG.md": "## [v1.1.0] - 2026-01-02\n"})

    assert check_version_sync.check_release_is_documented("1.0.0") == 0


def test_changes_outside_app_are_ignored(repo):
    """Docs, CI and deploy files are not what __version__ describes."""
    commit(repo, "docs tweak", {"docs/ARCHITECTURE.md": "text\n"})

    assert check_version_sync.check_release_is_documented("1.0.0") == 0


def test_missing_tag_skips_rather_than_fails(repo, capsys):
    """
    An unreleased bump and a shallow CI clone both look like this. Failing
    would block every release PR, since the tag is created after the merge.
    """
    commit(repo, "unreleased work", {"app/services/thing.py": "x = 1\n"})

    assert check_version_sync.check_release_is_documented("9.9.9") == 0
    assert "skipped" in capsys.readouterr().out


def test_skip_is_announced_not_silent(repo, capsys):
    check_version_sync.check_release_is_documented("9.9.9")

    output = capsys.readouterr().out
    assert "tag v9.9.9 not found" in output, "a silent skip reads as a pass in CI logs"


def test_outside_a_repository_the_check_declines(repo, monkeypatch):
    monkeypatch.setattr(check_version_sync, "PROJECT_ROOT", repo.parent)

    assert check_version_sync.check_release_is_documented("1.0.0") == 0


def test_git_helper_returns_none_when_git_is_missing(repo, monkeypatch):
    def no_git(*args, **kwargs):
        raise OSError("git not found")

    monkeypatch.setattr(subprocess, "run", no_git)

    assert check_version_sync.git("status") is None
