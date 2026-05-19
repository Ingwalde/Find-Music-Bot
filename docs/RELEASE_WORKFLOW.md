# Release Workflow

This project uses version tags and GitHub Releases.

## Version Format

The project uses semantic-style version names:

```text
v1.0.0
v1.1.0
v2.0.0
v2.1.0
v2.2.0
v2.2.1
v2.3.0
v2.4.1
```

## Before Creating a Release

1. Update `app/version.py`.
2. Update `README.md`.
3. Update `CHANGELOG.md`.
4. Update `docs/ROADMAP.md`.
5. Update release notes.
6. Run Ruff:

```bash
python -m ruff check .
```

7. Run tests with coverage:

```bash
python -m pytest
```

8. Run the release cleanup check:

```bash
python scripts/check_release_clean.py
```

9. For Docker releases, verify Docker build:

```bash
docker build -t find-music-bot:test .
```

10. Check that local/private files are not staged or tracked:

```text
.env
.git/
data/
logs/
__pycache__/
.pytest_cache/
.ruff_cache/
.vscode/
*.db
*.log
*.zip
coverage.xml
htmlcov/
```

## Commit Message Format

Use clear release commits:

```text
Release v2.4.1: expand coverage-focused tests
```

## Create Git Tag

```bash
git tag v2.4.1
git push origin v2.4.1
```

## Release Title Format

```text
v2.4.1 - Coverage Expansion Update
```

## Release Notes Template

```md
## Overview

Short explanation of this release.

## Added

- New files or features

## Changed

- Updated behavior or structure

## Fixed

- Bug fixes

## Quality Checks

- Ruff
- Pytest
- Coverage
- Release cleanup check
- Docker build

## Notes

Additional technical notes.
```

## Current Releases

```text
v1.0.0 - Deezer MVP
v1.1.0 - Pagination and History Update
v1.2.0 - UX Improvements
v1.3.0 - Track Metadata Update
v1.4.0 - Logging Update
v1.5.0 - Project Refactoring Update
v1.6.0 - Database Optimization Update
v1.7.0 - Tests Update
v1.8.0 - GitHub Polish Update
v1.9.0 - Multi-Language Update
v2.0.0 - Spotify API Integration
v2.1.0 - Architecture Cleanup Update
v2.2.0 - Stability, Testing & GitHub CI Update
v2.2.1 - GitHub Actions Runtime Update
v2.3.0 - Docker & Deployment Update
v2.4.1 - Coverage Expansion Update
```
