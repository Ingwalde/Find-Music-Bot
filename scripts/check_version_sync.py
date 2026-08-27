"""
Two checks that keep the release record honest.

1. app/version.py and the newest CHANGELOG.md entry must agree.

   Added in v3.7.8 after app/version.py sat at 3.7.0 through seven releases
   (v3.7.1 - v3.7.7) without anyone noticing. That value is user-visible: the
   /version command and the admin /maintenance report both read __version__,
   so the drift silently reported a wrong version to real users.

2. Changes under app/ since the last released tag must be documented.

   Check 1 alone has a blind spot: it compares the two files to each other, so
   it is satisfied the moment they match and cannot see work sitting *above*
   the newest entry. That is how the enforced layer boundary and the handlers
   split both reached main with no CHANGELOG line -- every check was green,
   because the only thing being compared was two already-agreeing values.

   This one compares against git instead: if the newest CHANGELOG version is
   already tagged and app/ has moved since that tag with CHANGELOG.md
   untouched, the release record is behind the code.
"""

import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_ROOT / "app" / "version.py"
CHANGELOG_FILE = PROJECT_ROOT / "CHANGELOG.md"

VERSION_PATTERN = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
CHANGELOG_PATTERN = re.compile(r"^##\s*\[v([0-9]+\.[0-9]+\.[0-9]+)\]", re.MULTILINE)


def read_module_version() -> str | None:
    if not VERSION_FILE.exists():
        return None

    match = VERSION_PATTERN.search(VERSION_FILE.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_changelog_version() -> str | None:
    if not CHANGELOG_FILE.exists():
        return None

    match = CHANGELOG_PATTERN.search(CHANGELOG_FILE.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def git(*args: str) -> str | None:
    """Runs a git command, returning None if git or the repository is unavailable."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    return result.stdout.strip() if result.returncode == 0 else None


def check_release_is_documented(version: str) -> int:
    """
    Fails when app/ has changed since tag v<version> but CHANGELOG.md has not.

    Skips silently when the tag is absent. That covers two legitimate cases:
    a release branch that has already bumped the version but not been tagged
    yet, and a shallow clone with no tags fetched. A skip is reported so a CI
    log never implies the check ran when it did not.
    """
    tag = f"v{version}"

    if git("rev-parse", "--verify", "--quiet", f"{tag}^{{commit}}") is None:
        print(f"Documentation check skipped: tag {tag} not found (unreleased or shallow clone).")
        return 0

    app_commits = git("log", "--format=%h", f"{tag}..HEAD", "--", "app/")
    if app_commits is None or not app_commits:
        return 0

    changelog_commits = git("log", "--format=%h", f"{tag}..HEAD", "--", "CHANGELOG.md")
    if changelog_commits:
        return 0

    changed = git("diff", "--name-only", f"{tag}..HEAD", "--", "app/") or ""
    files = [line for line in changed.splitlines() if line]

    print(
        f"FAIL: app/ has changed since {tag} but CHANGELOG.md has not.\n"
        f"  commits touching app/: {len(app_commits.splitlines())}\n"
        "  files:\n"
        + "".join(f"    {name}\n" for name in files[:20])
        + (f"    ... and {len(files) - 20} more\n" if len(files) > 20 else "")
        + "\n"
        "Undocumented work above the newest CHANGELOG entry is invisible to the\n"
        "version check, because that only compares app/version.py to the entry.\n"
        "Add a CHANGELOG entry (and bump app/version.py) for this work, or land\n"
        "it together with the release that documents it."
    )
    return 1


def main() -> int:
    module_version = read_module_version()
    changelog_version = read_changelog_version()

    if module_version is None:
        print("FAIL: could not read __version__ from app/version.py")
        return 1

    if changelog_version is None:
        print("FAIL: could not find a '## [vX.Y.Z]' heading in CHANGELOG.md")
        return 1

    if module_version != changelog_version:
        print(
            "FAIL: version mismatch.\n"
            f"  app/version.py  __version__ = {module_version!r}\n"
            f"  CHANGELOG.md    newest entry = v{changelog_version}\n"
            "\n"
            "__version__ is user-visible via /version and the admin /maintenance\n"
            "report. Bump app/version.py to match the release being cut."
        )
        return 1

    print(f"Version check passed. app/version.py and CHANGELOG.md agree on v{module_version}.")

    return check_release_is_documented(module_version)


if __name__ == "__main__":
    sys.exit(main())
