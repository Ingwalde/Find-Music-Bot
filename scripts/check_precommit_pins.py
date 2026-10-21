"""
Fails when .pre-commit-config.yaml and requirements/ disagree about a version.

The pre-commit hooks run in their own isolated environments, so every version
they need is written a second time in .pre-commit-config.yaml: the ruff hook's
`rev`, and the mypy hook's `additional_dependencies`. When one copy moves and
the other does not, a hook passes locally and the same check fails in CI, or
mypy resolves imports against a different library version than the app runs.

The pre-commit Dependabot ecosystem was added in v3.7.12 to stop that drift,
and it does open a PR for each copy — but nothing made the two PRs carry the
same version. In October it produced ruff 0.16.5 for requirements/dev.txt and
rev 0.17.1 for the hook, which is the exact divergence the ecosystem was added
to prevent, arriving as two green PRs instead of one silent edit.

Only pinned entries are checked. An entry with no version specifier, such as
types-python-dateutil, exists for the hook alone and has no counterpart to
agree with.

Stdlib only on purpose: the lint job would otherwise depend on PyYAML reaching
it transitively through pre-commit.
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRECOMMIT_FILE = PROJECT_ROOT / ".pre-commit-config.yaml"
BASE_REQUIREMENTS = PROJECT_ROOT / "requirements" / "base.txt"
DEV_REQUIREMENTS = PROJECT_ROOT / "requirements" / "dev.txt"

# `- repo: https://github.com/astral-sh/ruff-pre-commit` followed by its rev.
# The lookahead stops the search at the next `- repo:` line. Without it, a ruff
# block that had lost its rev would silently match the *following* repo's rev
# and compare mirrors-mypy's version against requirements' ruff pin.
RUFF_REV_PATTERN = re.compile(
    r"^\s*-\s*repo:\s*\S*ruff-pre-commit\s*$\n"
    r"(?:(?!\s*-\s*repo:).*\n)*?"
    r"\s*rev:\s*v?([^\s#]+)",
    re.MULTILINE,
)

# The indented list under `additional_dependencies:`, up to the next key.
ADDITIONAL_DEPS_PATTERN = re.compile(
    r"^(\s*)additional_dependencies:\s*$\n((?:\1\s+-\s*[^\n]+\n)+)",
    re.MULTILINE,
)

DEPENDENCY_LINE_PATTERN = re.compile(r"^\s*-\s*([A-Za-z0-9._-]+)\s*(.*?)\s*$")
REQUIREMENT_LINE_PATTERN = re.compile(r"^([A-Za-z0-9._-]+)\s*(.*?)\s*$")


def read_requirements() -> dict[str, str]:
    """Maps a package name to its version specifier across both requirement files."""
    pins: dict[str, str] = {}

    for path in (BASE_REQUIREMENTS, DEV_REQUIREMENTS):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue

            match = REQUIREMENT_LINE_PATTERN.match(line)
            if match and match.group(2):
                pins[match.group(1).lower()] = match.group(2)

    return pins


def check_ruff_rev(config: str, pins: dict[str, str], failures: list[str]) -> None:
    match = RUFF_REV_PATTERN.search(config)
    if match is None:
        failures.append(
            "could not find the ruff-pre-commit hook's rev in "
            ".pre-commit-config.yaml — this checker needs updating, not skipping"
        )
        return

    hook_version = match.group(1)
    required = pins.get("ruff")

    if required is None:
        failures.append("ruff is pinned in .pre-commit-config.yaml but not in requirements/")
        return

    if required != f"=={hook_version}":
        failures.append(
            f"ruff: hook rev is v{hook_version}, requirements say ruff{required}.\n"
            "    A hook running a different ruff than CI can pass locally and fail "
            "there, or the reverse."
        )


def check_additional_dependencies(
    config: str, pins: dict[str, str], failures: list[str]
) -> None:
    blocks = ADDITIONAL_DEPS_PATTERN.findall(config)
    if not blocks:
        failures.append(
            "could not find an additional_dependencies block in "
            ".pre-commit-config.yaml — this checker needs updating, not skipping"
        )
        return

    checked = 0

    for _indent, block in blocks:
        for raw_line in block.splitlines():
            match = DEPENDENCY_LINE_PATTERN.match(raw_line)
            if match is None:
                continue

            name, specifier = match.group(1), match.group(2)
            if not specifier:
                # Hook-only tooling such as types-python-dateutil.
                continue

            checked += 1
            required = pins.get(name.lower())

            if required is None:
                failures.append(
                    f"{name}: pinned as {name}{specifier} for the mypy hook but absent "
                    "from requirements/"
                )
            elif required != specifier:
                failures.append(
                    f"{name}: mypy hook uses {name}{specifier}, requirements say "
                    f"{name}{required}.\n"
                    "    mypy would resolve this library's types at a different "
                    "version than the app installs."
                )

    if checked == 0:
        failures.append(
            "found additional_dependencies but no pinned entries in it — "
            "a silent pass here would hide every future mismatch"
        )


def main() -> int:
    config = PRECOMMIT_FILE.read_text(encoding="utf-8")
    pins = read_requirements()
    failures: list[str] = []

    check_ruff_rev(config, pins, failures)
    check_additional_dependencies(config, pins, failures)

    if failures:
        print("FAIL: .pre-commit-config.yaml and requirements/ disagree.\n")
        for failure in failures:
            print(f"  - {failure}")
        print(
            "\nEvery version in .pre-commit-config.yaml is a second copy of one in\n"
            "requirements/. Dependabot opens a separate PR for each copy, so the two\n"
            "have to be merged together — or the pin updated by hand to match."
        )
        return 1

    print("Pre-commit pin check passed. Hook versions match requirements/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
