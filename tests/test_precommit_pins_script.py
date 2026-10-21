"""
Covers scripts/check_precommit_pins.py.

Written against the real divergence that prompted it: Dependabot opened ruff
0.16.5 for requirements/dev.txt and hook rev 0.17.1 as two separate green PRs,
so merging both would have left the hook running a different ruff than CI.
"""

import pytest

from scripts import check_precommit_pins as checker

CONFIG_TEMPLATE = """\
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v{ruff_rev}
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v2.3.1
    hooks:
      - id: mypy
        pass_filenames: false
        additional_dependencies:
{additional}

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-yaml
"""


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Writes a minimal, self-consistent project and points the checker at it."""
    requirements = tmp_path / "requirements"
    requirements.mkdir()

    def build(
        ruff_rev="0.16.3",
        additional=("aiogram==3.30.0", "fastapi==0.141.1", "types-python-dateutil"),
        base=("aiogram==3.30.0", "fastapi==0.141.1"),
        dev=("ruff==0.16.3", "mypy>=2.3.1"),
    ):
        config = tmp_path / ".pre-commit-config.yaml"
        config.write_text(
            CONFIG_TEMPLATE.format(
                ruff_rev=ruff_rev,
                additional="\n".join(f"          - {entry}" for entry in additional),
            ),
            encoding="utf-8",
        )
        (requirements / "base.txt").write_text("\n".join(base) + "\n", encoding="utf-8")
        (requirements / "dev.txt").write_text("\n".join(dev) + "\n", encoding="utf-8")

        monkeypatch.setattr(checker, "PRECOMMIT_FILE", config)
        monkeypatch.setattr(checker, "BASE_REQUIREMENTS", requirements / "base.txt")
        monkeypatch.setattr(checker, "DEV_REQUIREMENTS", requirements / "dev.txt")

    return build


def test_matching_versions_pass(project):
    project()

    assert checker.main() == 0


def test_the_real_ruff_divergence_fails(project, capsys):
    """requirements 0.16.5 against hook rev 0.17.1 — October 2026, PRs #83 and #94."""
    project(ruff_rev="0.17.1", dev=("ruff==0.16.5", "mypy>=2.3.1"))

    assert checker.main() == 1

    output = capsys.readouterr().out
    assert "hook rev is v0.17.1" in output
    assert "ruff==0.16.5" in output


def test_additional_dependency_mismatch_fails(project, capsys):
    project(
        additional=("aiogram==3.31.0", "fastapi==0.141.1"),
        base=("aiogram==3.30.0", "fastapi==0.141.1"),
    )

    assert checker.main() == 1
    assert "aiogram" in capsys.readouterr().out


def test_pinned_hook_dependency_missing_from_requirements_fails(project, capsys):
    project(additional=("aiogram==3.30.0", "prometheus-client==0.26.0"))

    assert checker.main() == 1
    assert "prometheus-client" in capsys.readouterr().out


def test_unpinned_hook_only_dependency_is_ignored(project):
    """types-python-dateutil has no counterpart to agree with."""
    project(additional=("aiogram==3.30.0", "types-python-dateutil"))

    assert checker.main() == 0


def test_range_specifiers_must_match_verbatim(project):
    project(
        additional=("aiogram==3.30.0", "redis>=8.1.0,<9.0.0"),
        base=("aiogram==3.30.0", "redis>=8.1.0,<9.0.0"),
    )

    assert checker.main() == 0


def test_differing_range_specifier_fails(project, capsys):
    project(
        additional=("aiogram==3.30.0", "redis>=8.2.0,<9.0.0"),
        base=("aiogram==3.30.0", "redis>=8.1.0,<9.0.0"),
    )

    assert checker.main() == 1
    assert "redis" in capsys.readouterr().out


def test_comments_and_blank_lines_in_requirements_are_ignored(project):
    project(dev=("# linting", "", "ruff==0.16.3", "mypy>=2.3.1"))

    assert checker.main() == 0


# -- the checker must not pass by failing to find anything --------------------


def test_missing_ruff_hook_is_reported_not_skipped(project, capsys, monkeypatch):
    project()
    config = checker.PRECOMMIT_FILE
    config.write_text(
        config.read_text(encoding="utf-8").replace("ruff-pre-commit", "something-else"),
        encoding="utf-8",
    )

    assert checker.main() == 1
    assert "needs updating, not skipping" in capsys.readouterr().out


def test_ruff_rev_search_does_not_leak_into_the_next_repo(project, capsys):
    """
    A ruff block with no rev must report that, not borrow the next repo's.

    The first version of the pattern spanned lines with `(?:.*\\n)*?`, so it
    matched mirrors-mypy's rev and compared v2.4.0 against requirements' ruff
    pin — a wrong answer dressed as a real finding.
    """
    project()
    config = checker.PRECOMMIT_FILE
    config.write_text(
        config.read_text(encoding="utf-8").replace("    rev: v0.16.3\n", "", 1),
        encoding="utf-8",
    )

    assert checker.main() == 1

    output = capsys.readouterr().out
    assert "needs updating, not skipping" in output
    assert "2.3.1" not in output, "it picked up the mypy hook's rev instead"


def test_missing_additional_dependencies_block_is_reported(project, capsys):
    project()
    config = checker.PRECOMMIT_FILE
    text = config.read_text(encoding="utf-8")
    start = text.index("        additional_dependencies:")
    end = text.index("  - repo: https://github.com/pre-commit/pre-commit-hooks")
    config.write_text(text[:start] + text[end:], encoding="utf-8")

    assert checker.main() == 1
    assert "could not find an additional_dependencies block" in capsys.readouterr().out


def test_block_with_no_pinned_entries_is_reported(project, capsys):
    project(additional=("types-python-dateutil",))

    assert checker.main() == 1
    assert "no pinned entries" in capsys.readouterr().out
