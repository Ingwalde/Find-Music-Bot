"""
Fails when app/version.py and the newest CHANGELOG.md entry disagree.

Added in v3.7.8 after app/version.py sat at 3.7.0 through seven releases
(v3.7.1 - v3.7.7) without anyone noticing. That value is user-visible: the
/version command and the admin /maintenance report both read __version__, so
the drift silently reported a wrong version to real users.
"""

import re
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
