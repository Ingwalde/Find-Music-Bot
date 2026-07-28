"""Validate that private/local files are not tracked by Git.

This script is designed for CI and release checks. It checks tracked files
(`git ls-files`) instead of every local file, so developers may still keep a
local `.env`, local logs or a local SQLite database outside Git.
"""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

ALLOWED_EXACT = {".env.example"}

FORBIDDEN_EXACT = {
    ".env",
    "pytest.ini",  # pytest config is kept in pyproject.toml
}

FORBIDDEN_DIRS = (
    "data/",
    "logs/",
    "certs/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    ".vscode/",
    ".idea/",
)

FORBIDDEN_PATTERNS = (
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.log",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.7z",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
)


def get_tracked_files() -> list[str]:
    """Return files currently tracked by Git."""
    result = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def is_forbidden(path: str) -> bool:
    normalized = path.replace("\\", "/")

    if normalized in ALLOWED_EXACT:
        return False

    if normalized in FORBIDDEN_EXACT:
        return True

    if normalized.startswith(".env."):
        return True

    parts = normalized.split("/")
    if "__pycache__" in parts:
        return True

    for directory in FORBIDDEN_DIRS:
        if normalized == directory.rstrip("/") or normalized.startswith(directory):
            return True

    filename = Path(normalized).name
    return any(
        fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(normalized, pattern)
        for pattern in FORBIDDEN_PATTERNS
    )


def main() -> int:
    try:
        tracked_files = get_tracked_files()
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"Release cleanup check failed: could not read tracked files: {error}")
        return 2

    forbidden = sorted(path for path in tracked_files if is_forbidden(path))

    if forbidden:
        print("Release cleanup check failed. These forbidden files are tracked by Git:")
        for path in forbidden:
            print(f"- {path}")
        print("\nRemove them from Git tracking and keep them ignored in .gitignore.")
        return 1

    print("Release cleanup check passed. No forbidden local/private files are tracked by Git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
