# Changelog

All notable changes to this project will be documented in this file.

---

## [v2.4.0] - 2026-05-19

### Added
- Added pytest coverage reporting through `pytest-cov`.
- Added coverage configuration to `pyproject.toml`.
- Added `scripts/check_release_clean.py` for release safety validation.
- Added release cleanup validation step to GitHub Actions.

### Changed
- Updated project version to `2.4.0`.
- Updated README with coverage and release cleanup instructions.
- Updated release workflow documentation with coverage and cleanup checks.
- Updated roadmap for the v2.4 quality release and v2.5 admin/database maintenance plan.
- Improved `.gitignore` and `.dockerignore` for coverage artifacts and local archives.

### Notes
- This release focuses on code quality, coverage reporting and clean release packaging.
- No new music platforms were added.
- Main bot behavior remains unchanged.

---

## [v2.3.0] - 2026-05-12

### Added
- Added `Dockerfile` for containerized bot startup.
- Added `docker-compose.yml` for one-command local Docker startup.
- Added `.dockerignore` to keep local/private files out of Docker builds.
- Added `docs/DEPLOYMENT.md` with local, Docker and Docker Compose instructions.
- Added Docker build validation step to GitHub Actions.
- Added GitHub Actions badge to README.

### Changed
- Updated project version to `2.3.0`.
- Updated README with Docker usage instructions.
- Updated `.env.example` with clearer configuration descriptions.
- Updated roadmap and release workflow documentation.

### Notes
- This release focuses on deployment readiness.
- No new music platforms were added.
- Main bot behavior remains unchanged.

---

## [v2.2.1] - 2026-05-12

### Changed
- Updated GitHub Actions workflow to use Node.js 24-compatible action versions.
- Updated `actions/checkout` from `v4` to `v6`.
- Updated `actions/setup-python` from `v5` to `v6`.
- Added pip dependency caching to the Python setup step.
- Added Ruff check step to the GitHub Actions workflow.
- Updated project version to `2.2.1`.

### Fixed
- Removed GitHub Actions warning about deprecated Node.js 20 action runtime.
- Ensured CI checks run both Ruff and pytest.

### Notes
- This is a patch release. It does not change bot features or user-facing behavior.

---

## [v2.2.0] - 2026-05-12

### Added
- Added `.github/workflows/tests.yml` for GitHub Actions test automation.
- Added `pyproject.toml` with pytest and Ruff configuration.
- Added `requirements-dev.txt` for development tooling.
- Added `app/health.py` with bot, database, Deezer, Spotify and Genius diagnostics.
- Added admin `/health` command.
- Added tests for health report formatting.
- Added tests for Spotify fallback behavior in the platform aggregator.

### Changed
- Updated project version to `2.2.0`.
- Improved Deezer search error handling.
- Improved Deezer track loading error handling.
- Updated README for the v2.2.0 release.
- Updated roadmap and release workflow documentation.

### Fixed
- Fixed duplicated `admin_only` response in the `/errors` command.
- Ensured Spotify failures do not break track cards or Deezer-based results.

### Security
- Release package should not include `.env`, `.git`, `data/`, `logs/`, `.pytest_cache`, `.vscode` or `__pycache__` files.

---

## [v2.1.0] - 2026-04-30

### Added
- Added `app/database/schema.py`.
- Added `app/database/migrations.py`.
- Added `app/database/indexes.py`.
- Added split repository modules under `app/database/repository_modules/`.
- Added split localization files under `app/localization/locales/`.
- Added `app/localization/translator.py`.
- Added platform layer under `app/platforms/`.
- Added Spotify platform modules:
  - `app/platforms/spotify/auth.py`
  - `app/platforms/spotify/client.py`
  - `app/platforms/spotify/matcher.py`
- Added `app/platforms/aggregator.py`.
- Added architecture import tests.

### Changed
- `app/database/db.py` now coordinates schema, migrations and indexes instead of containing everything.
- `app/database/repositories.py` is now a compatibility facade.
- `app/database/spotify_repository.py` is now a compatibility facade.
- `app/localization/translations.py` is now a compatibility facade.
- `app/services/spotify_service.py` is now a compatibility facade.
- `app/services/track_platform_service.py` is now a compatibility facade.
- Improved project maintainability after Spotify API integration.

### Notes
This release does not add major user-facing features. It focuses on internal architecture and long-term maintainability.
