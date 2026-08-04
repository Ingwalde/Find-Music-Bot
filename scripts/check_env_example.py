"""Verify that every os.getenv() call in app/ has a matching entry in .env.example.

Exits with code 1 and lists missing variables if any are found.
Runs in CI as a gate — prevents undocumented environment variables from shipping.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

_GETENV_RE = re.compile(r'os\.getenv\(\s*["\']([A-Z_][A-Z0-9_]*)["\']')

SKIP_VARS = {
    "ALEMBIC_DATABASE_URL",  # set programmatically by conftest; never in .env
    "GENIUS",                # legacy alias for GENIUS_TOKEN; users set GENIUS_TOKEN
}


def _collect_getenv_vars() -> set[str]:
    found: set[str] = set()
    for py_file in APP_DIR.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        for match in _GETENV_RE.finditer(source):
            found.add(match.group(1))
    return found - SKIP_VARS


def _collect_env_example_vars() -> set[str]:
    documented: set[str] = set()
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        # Accept both active lines (VAR=value) and commented-out examples (# VAR=value).
        # Plain prose comments have no "=" so they never match the var-name regex.
        stripped = line.lstrip("#").strip()
        if "=" not in stripped:
            continue
        var = stripped.split("=", 1)[0].strip()
        if re.match(r"^[A-Z_][A-Z0-9_]*$", var):
            documented.add(var)
    return documented


def main() -> None:
    getenv_vars = _collect_getenv_vars()
    documented = _collect_env_example_vars()
    missing = getenv_vars - documented

    if not missing:
        print(f"OK — all {len(getenv_vars)} env vars documented in .env.example")
        return

    print(f"FAIL — {len(missing)} env var(s) missing from .env.example:")
    for var in sorted(missing):
        print(f"  - {var}")
    sys.exit(1)


if __name__ == "__main__":
    main()
