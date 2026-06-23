# Changelog

All notable changes to this project will be documented in this file.

---

## [v3.2.0] - 2026-06-23

### Added
- HTTP monitoring endpoints via FastAPI alongside the bot's polling: GET /health (liveness)
  and GET /ready (PostgreSQL readiness), port 9090.

### Changed
- `docker-compose.yml` moved from `deploy/` to the project root (plain `docker compose`, no
  `-f`/`--env-file` flags). Dockerfile stays in `deploy/`.
- Dockerfile execs the bot as PID 1 so SIGTERM reaches it (graceful shutdown now works).

### Notes
- No user-facing change; the bot stays on aiogram polling. Endpoints are for Docker
  healthchecks and external uptime monitoring. Webhooks remain a future release.

---

## [v3.1.1] - 2026-06-19

### Changed
- Replaced the hand-built schema-migration mechanism with Alembic (industry-standard tooling).
  Alembic now owns the database schema; the app runtime stays on asyncpg. Schema is applied via
  `alembic upgrade head` at container start.
- Retired `create_tables_pg`/`create_indexes_pg`/`migrate_db`; `init_db_pool()` now only creates
  the connection pool.
- `get_schema_version()` now returns the app version directly.
- Fixed a facade-rule violation: `aggregator.py` now imports through the `spotify_repository`
  facade.

### Notes
- Backend tooling change, no user-facing effect. Existing data untouched; the live database was
  stamped at the Alembic baseline.

---

## [v3.1.0] - 2026-06-17

### Changed
- Migrated the database from SQLite to PostgreSQL (asyncpg). All database access is now
  fully asynchronous via a connection pool; SQLite code has been removed from the application.
- Repository modules, maintenance layer, error logging, platform aggregator, and health checks
  all operate against PostgreSQL through the shared asyncpg pool.
- `app/main.py` now calls `await init_db_pool()` at startup and `await close_db_pool()` in the
  finally block; the sync `init_db()` call has been removed.
- `asyncio.to_thread` wrappers around database calls removed across the bot layer (handlers,
  callbacks, services) — all DB calls are now natively async.
- `DATABASE_URL` is now required — `settings.validate()` raises `ValueError` if it is missing.

### Added
- PostgreSQL service in `deploy/docker-compose.yml` (postgres:16-alpine) with a `pg_isready`
  healthcheck; bot service depends on `service_healthy`.
- Named volume `postgres-data` for persistent PostgreSQL data.
- `scripts/migrate_sqlite_to_postgres.py` — one-time standalone migration script that reads
  the existing SQLite file (read-only), creates the PG schema, migrates all tables in FK-safe
  order preserving explicit IDs, resets BIGSERIAL sequences, and verifies row counts.

### Notes
- No user-facing feature changes; this is a database backend migration.
- Existing data is preserved via the migration script before switching to PostgreSQL.
- `migrations.py` is kept in place but unreferenced by the application (Stage 12 handles it).
- Tests run against a real PostgreSQL instance via testcontainers.

---

## [v3.0.1] - 2026-06-16

### Changed
- Wrapped two remaining synchronous SQLite calls in `recommendations_service.py` (`get_db_recommendations`, `get_similar_by_genre`) in `asyncio.to_thread` so they no longer briefly block the event loop during recommendation and `/similar` queries.

### Notes
- Internal async hygiene patch — no behavior change for users.
- Test coverage unchanged (312 tests, all passing).

---

## [v3.0.0] - 2026-06-16

### Breaking Changes
- **Migrated from pyTelegramBotAPI to aiogram 3.29.0.** All bot handlers, callbacks, and lifecycle code are now fully async. Any custom fork relying on the sync telebot API must be updated.
- Removed dependencies: `pyTelegramBotAPI`, `deezer-python`, `lyricsgenius`, `requests`.

### Changed
- All bot-layer functions are now `async def` using `asyncio.to_thread` for sync DB/IO calls.
- `app/main.py` now wires `handlers_router` and `callbacks_router` into an aiogram `Dispatcher` and calls `bot.delete_webhook(drop_pending_updates=True)` before polling.
- `app/database/repository_modules/users.py` now imports `User` from `aiogram.types` instead of `telebot.types`.
- Deezer search rewritten with `httpx` (async HTTP, no SDK). Lyrics rewritten with `httpx` direct API. Spotify platform unchanged.

### Fixed
- Fixed track card never reaching the user when a track button was tapped — `send_track_card` in `track_callbacks.py` was called without `await`, silently discarding the coroutine. Caught during aiogram migration smoke testing.

### Notes
- Database schema and SQLite file format unchanged — no migration needed.
- Test coverage remains ≥ 93% (312 tests, all passing).
- All localization keys and 8 supported languages unchanged.

---

## [v2.7.0] - 2026-06-12

### Changed
- Removed unreachable dead-code branches from `process_music_search` (menu-button and `/start` handling, already covered by `text_handler` routing).
- `/similar` and `/trending` now reuse `format_similar_text` and `format_recommendations_text` from `recommendations_service.py` instead of duplicating list-formatting logic. `/similar` output now uses the same grouped `🎤 Artist / 🎵 Others` format as the inline 🎯 Similar button.
- Fixed a `seen_ids` collision in `get_similar_by_genre` where tracks without a `deezer_track_id` could block all related-artist candidates.
- Removed unused compatibility-facade exports from `repositories.py` (`row_to_dict`, `trim_search_history`, `get_table_counts`, `get_schema_version`).
- Extracted `get_user_context()` helper (registers the user and returns their language) used across ~19 handlers.
- Extracted `require_admin()` helper for the 8 admin-only command handlers.
- All repository functions and `init_db()` now close their SQLite connection in a `finally` block, guaranteeing cleanup even if an error occurs.

### Notes
- Internal refactor only — no user-facing feature changes besides the `/similar` formatting unification above.
- Test coverage remains at 93.50% (minimum 85%).

---

## [v2.6.1] - 2026-06-11

### Fixed
- Localized favorites error alerts (were shown in English for all languages)
- Localized version command output
- Added error handling to language selection callback

### Changed
- Track card errors now logged to admin error log (were only logged to file)

### Notes
- Improved test coverage for favorites and history callbacks

---

## [v2.6.0] - 2026-06-09

### Added
- Added `/similar` command — finds tracks similar to the last viewed track using the Deezer radio endpoint (`/track/{id}/radio`).
- Added `/trending` command — shows top tracks of the week via the Deezer chart endpoint (`/chart/0/tracks`).
- Added "You may also like" block sent after each track card based on artist from local DB with fallback to Deezer artist top tracks.
- Added 🎯 Similar inline button on every track card for quick access to similar tracks.
- Added `last_track_id` persistence to the `users` table in SQLite so `/similar` works across sessions.
- Added `get_similar_tracks()`, `get_trending_tracks()`, `get_artist_top_tracks()` to `deezer_service.py`.
- Added `recommendations_service.py` with in-memory trending cache (1-hour TTL) and DB-first recommendation logic.
- Added `similar_callbacks.py` for the 🎯 Similar button callback handler.
- Added `get_tracks_by_artist()` to tracks repository and facade.
- Added `save_last_track_id()` / `get_last_track_id()` to users repository and facade.
- Added localization keys for all 8 languages: `similar_header`, `similar_empty`, `similar_no_context`, `trending_header`, `trending_empty`, `you_may_also_like`, `btn_similar`.
- Updated `/help` command text with new commands in all 8 supported languages.

### Fixed
- Fixed: infinite "menu buttons disabled" loop — users can now open Favorites/History directly while in search mode.
- Removed redundant next-step handler that caused message quote linking in search mode.

### Notes
- Trending results are cached in-memory for 1 hour to reduce Deezer API load.
- "You may also like" queries the local SQLite DB first; Deezer artist API is used as fallback only when no local data is found.
- `last_track_id` is stored in the database so it persists across bot restarts.

---

## [v2.5.2] - 2026-06-04

### Added
- Added lazy Deezer client initialization to avoid import-time client side effects.
- Added lazy Genius client initialization to avoid startup warnings when lyrics are not configured.
- Added thread-safe locking around in-memory search contexts.
- Added localized admin reports and an admin cache reload action.
- Added locale coverage checker script.
- Added `deploy/` and `requirements/` folders for cleaner project layout.

### Changed
- Moved production dependencies to `requirements/base.txt`.
- Moved development dependencies to `requirements/dev.txt`.
- Moved Docker configuration to `deploy/Dockerfile` and `deploy/docker-compose.yml`.
- Updated Docker, setup and development documentation for the new deploy/requirements layout.
- Reworked README into a full project overview instead of a version-by-version release summary.
- Updated project version to `2.5.2`.

### Fixed
- Fixed Ruff `E402` issue in the locale coverage checker.
- Fixed admin report tests after adding localized Spotify status formatting.

### Notes
- The old root `Dockerfile`, `docker-compose.yml`, `requirements.txt`, and `requirements-dev.txt` can be removed after applying this update.
- This release does not add new music platforms.

---

## [v2.5.1] - 2026-05-21

### Added
- Added cached admin ID loading with `clear_admin_ids_cache()` for tests and runtime reload scenarios.
- Added TTL-based cleanup for in-memory search contexts.
- Added dynamic database maintenance table discovery from SQLite schema.
- Added localized `btn_open_genius` translation key for the Genius lyrics URL button.
- Added tests for admin cache behavior, context expiration, dynamic maintenance table discovery, localized Genius button and Spotify runtime lock behavior.
- Added `docs/CODE_REVIEW_ACTION_PLAN.md` to document the review-based improvement roadmap.

### Changed
- Updated project version to `2.5.1`.
- Replaced the lazy `app.bot.handlers` import inside `actions.py` with an explicit music search handler registration.
- Wrapped Spotify token/cache/cooldown runtime state in a reentrant lock for safer threaded handler execution.
- Updated README, roadmap, architecture and release workflow documentation.

### Fixed
- Fixed hardcoded English Genius button text by using the existing localization system.
- Fixed admin button visibility after language switching.
- Fixed admin menu buttons not following the selected language.
- Reduced repeated file I/O by caching admin IDs instead of loading `config/admins.json` on each admin check.
- Reduced risk of unbounded memory growth from stale search pagination contexts.

### Notes
- This patch is based on the external code review findings.
- No new music platforms were added.
- The main bot behavior remains unchanged.

---

## [v2.5.0] - 2026-05-21

### Added
- Added `app/database/maintenance.py` with database size, table counts, schema version and cleanup helpers.
- Added `app/admin_tools.py` with admin statistics, maintenance and cleanup report formatting.
- Added admin `/stats` command.
- Added admin `/maintenance` command.
- Added admin `/cleanup_errors` command.
- Added admin `/cleanup_history` command.
- Added admin menu button visibility based on `config/admins.json`.
- Added admin menu keyboard for stats, maintenance, cleanup and health actions.
- Added `config/admins.example.json` as a safe template for local admin IDs.
- Added `schema_migrations` table for schema version visibility.
- Added tests for database maintenance helpers.
- Added tests for admin reports and admin command handlers.

### Changed
- Updated project version to `2.5.0`.
- Updated README with admin maintenance commands.
- Updated architecture and roadmap documentation for database maintenance.
- Updated release workflow documentation with v2.5 release checks.
- Updated English help text with admin diagnostics commands.
- Updated main menu rendering to show the admin button only for allowed Telegram IDs.

### Notes
- This release focuses on database maintenance and admin tooling.
- No new music platforms were added.
- Main user-facing music search behavior remains unchanged.

---

## [v2.4.1] - 2026-05-21

### Added
- Added additional tests for runtime startup, database repositories, Deezer service and Spotify auth/client behavior.

### Changed
- Updated project version to `2.4.1`.
- Increased full-project coverage from 85% to 93.40%.
- Expanded the test suite from 169 to 196 tests.
- Added and verified a minimum coverage gate of 85%.

### Notes
- This patch release focuses on coverage expansion only.
- Main bot behavior remains unchanged.

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
- This release focuses on architecture and maintainability.
