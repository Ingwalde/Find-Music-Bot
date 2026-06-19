# Architecture

## Overview

The bot is split into layers:

```text
Telegram Bot Layer
 ↓
Bot Actions / Callback Router / Admin Commands
 ↓
Services / Platform Aggregator / Admin Tools
 ↓
Database Repositories / Maintenance Helpers
 ↓
PostgreSQL  (asyncpg connection pool)
```

## Bot Layer

```text
app/bot/
```

Contains Telegram handlers, callbacks and keyboard builders.

Admin-only commands are registered in `app/bot/handlers.py` and use `ADMIN_ID` from settings.

## Admin Tools Layer

```text
app/admin_tools.py
```

Formats operational reports for admin commands:

```text
/stats
/maintenance
/cleanup_errors
/cleanup_history
```

This layer keeps Telegram command handlers small and moves report formatting into testable functions.

## Platform Layer

```text
app/platforms/
```

Contains platform-specific integrations.

```text
app/platforms/spotify/auth.py     → token, cooldown, API access errors
app/platforms/spotify/client.py   → Spotify Web API search
app/platforms/spotify/matcher.py  → text normalization and result scoring
app/platforms/aggregator.py       → enriches tracks with optional platform links
```

## Database Layer

```text
app/database/
```

Database logic is split into:

```text
db.py           → asyncpg pool singleton, init_db_pool(), close_db_pool()
maintenance.py  → database size, table counts, cleanup helpers and schema version visibility
```

Schema is owned by Alembic (v3.1.1+) — see `migrations/versions/` at the project root, not
`app/database/`. `schema.py`, `indexes.py`, and `migrations.py` were retired in v3.1.1;
`init_db_pool()` now only creates the connection pool. See "v3.1.1 Alembic Migration Tooling"
below.

Repository functions are split by domain:

```text
repository_modules/users.py
repository_modules/searches.py
repository_modules/tracks.py
repository_modules/favorites.py
repository_modules/errors.py
repository_modules/spotify.py
```

`repositories.py` remains as a compatibility facade.

## Schema Version Visibility

Version `v2.5.0` added a lightweight `schema_migrations` table, written by the app on every
startup. As of v3.1.1, schema versioning is owned by Alembic (its own `alembic_version` table),
and nothing in the app writes to `schema_migrations` anymore — it is kept in place as an
untouched legacy table. `get_schema_version()` (`app/database/maintenance.py`) now returns the
running app version directly instead of querying it, since that query could only ever return a
frozen, increasingly stale value. The admin `/maintenance` command still shows a "schema
version" — it now means "the version of code currently running," not a separate schema history.

## Localization Layer

```text
app/localization/
```

```text
translator.py       → t() and menu action detection
locales/en.py       → default English translations
locales/*.py        → language overrides
```

English is the fallback language.

## Compatibility Facades

Several old files remain as facades so existing imports continue to work:

```text
app/database/repositories.py
app/database/spotify_repository.py
app/localization/translations.py
app/services/spotify_service.py
app/services/track_platform_service.py
```

## Health Diagnostics

```text
app/health.py
```

The health module provides admin diagnostics for:

- bot runtime status;
- PostgreSQL database connectivity (pool health);
- Deezer service import availability;
- Spotify configuration and temporary cooldown state;
- Genius token configuration.

The Telegram `/health` command is admin-only and is designed for quick operational checks without exposing secrets.

## Database Maintenance Diagnostics

```text
app/database/maintenance.py
```

The maintenance module provides:

- database file size;
- row counts for important tables;
- schema version visibility;
- cleanup helpers for saved errors;
- cleanup helpers for search history.

These helpers are used by admin commands and covered by tests.

## CI Layer

```text
.github/workflows/tests.yml
pyproject.toml
requirements/dev.txt
```

GitHub Actions runs automated checks on pushes and pull requests to `main` and `master`:

```text
Ruff
pytest with coverage
release cleanup check
Docker build
```

## Deployment Layer

```text
deploy/Dockerfile
deploy/docker-compose.yml
.dockerignore
docs/DEPLOYMENT.md
```

The deployment layer allows the bot to run in a containerized environment while keeping runtime data outside the image:

```text
data/ -> SQLite file (kept for migration; removed after cutover)
logs/ -> runtime logs
```

Docker Compose uses `.env` for configuration and mounts `data/` and `logs/` as local volumes.
The Postgres service uses a named volume (`postgres-data`) for persistent data and a `pg_isready`
healthcheck; the bot service depends on `service_healthy`.

---

## Quality and Release Safety

```text
scripts/
├── check_release_clean.py          # Validates that private/local files are not tracked by Git
└── migrate_sqlite_to_postgres.py   # One-time SQLite → PostgreSQL data migration
```

The cleanup script checks tracked files only. This allows developers to keep local `.env`, logs and data files in the working directory while preventing them from being committed or released.


## Admin access configuration

Admin menu visibility is controlled by local admin IDs from `config/admins.json` or the legacy `ADMIN_ID` environment variable. `config/admins.json` must stay local and is ignored by Git.

## v2.5.1 Stability Cleanup

Version `v2.5.1` addresses review-driven stability issues without changing the main user-facing bot behavior:

- admin IDs are cached after loading from `config/admins.json`;
- Spotify token/cache/cooldown runtime state is protected by a reentrant lock;
- in-memory search contexts include a TTL and are cleaned lazily;
- `actions.py` no longer imports `handlers.py` through a lazy import workaround;
- maintenance table reporting discovers tables from SQLite schema;
- the Genius URL button uses the existing localization system.

The larger structural refactor is intentionally moved to `v2.6.0` to keep this patch release focused and safe.

## v2.6.0 Smart Recommendations

Version `v2.6.0` adds smart music recommendations without changing the core search or track card flow:

- `app/services/deezer_service.py` gains three new functions: `get_similar_tracks()` (Deezer radio endpoint), `get_trending_tracks()` (Deezer chart endpoint), and `get_artist_top_tracks()` (Deezer artist search + top endpoint).
- `app/services/recommendations_service.py` is a new service module that orchestrates DB-first recommendations with Deezer fallback, manages an in-memory trending cache (1-hour TTL), and formats recommendation text for display.
- `app/bot/similar_callbacks.py` is a new callback handler for the 🎯 Similar inline button.
- The `users` table gains a `last_track_id` column (TEXT, nullable) to persist the last viewed track across sessions. A corresponding lightweight migration is added to `migrations.py`.
- `repository_modules/users.py` adds `save_last_track_id()` and `get_last_track_id()`. `repository_modules/tracks.py` adds `get_tracks_by_artist()`. Both are exposed through the `repositories.py` facade.

## v2.5.2 Runtime and Layout Cleanup

Version `v2.5.2` adds small runtime polish and project layout cleanup without changing the main bot behavior:

- Deezer and Genius clients are initialized lazily instead of during module import.
- Search contexts are guarded by a lock for safer threaded handler execution.
- Admin statistics and maintenance reports support localization keys.
- Admin cache can be reloaded without restarting the bot.
- Runtime/deployment files are grouped under `deploy/`.
- Production and development dependency files are grouped under `requirements/`.
- Locale override coverage can be inspected with `scripts/check_locale_coverage.py`.

## v2.6.1 Localization and Error Logging Fixes

Version `v2.6.1` is a maintenance patch and does not change the core architecture:

- Favorites error alerts and the `/version` command output are now localized across all 8 supported languages.
- Track card errors (cover image, recommendations, last_track_id) are now routed to the admin error log via `log_and_save_error` instead of file-only logging.
- Added error handling to the language selection callback.

## v2.7.0 Bot Structure Refactor

Version `v2.7.0` is an internal technical-debt refactor and does not change the layered architecture or user-facing behavior beyond the `/similar` formatting unification below:

- `app/bot/handlers.py` gains two shared helpers: `get_user_context(message)` (registers the user and returns their language, replacing a repeated two-line pattern across ~19 handlers) and `require_admin(bot, message, language)` (replaces the repeated admin-check pattern in the 8 admin-only command handlers).
- `process_music_search` no longer contains unreachable branches — menu-button and `/start` routing is handled exclusively by `text_handler`.
- `/similar` and `/trending` now call `format_similar_text` / `format_recommendations_text` from `app/services/recommendations_service.py` instead of duplicating list-formatting logic; `/similar` output is now grouped as `🎤 Artist / 🎵 Others`, matching the inline 🎯 Similar button.
- `get_similar_by_genre` no longer treats tracks with a missing `deezer_track_id` as duplicates of each other.
- The compatibility facade `app/database/repositories.py` no longer re-exports unused internal helpers (`row_to_dict`, `trim_search_history`, `get_table_counts`, `get_schema_version`).
- All repository functions in `repository_modules/` and `database/maintenance.py`, plus `init_db()`, now close their SQLite connection in a `finally` block.

## v3.0.0 aiogram Migration

Version `v3.0.0` replaces pyTelegramBotAPI with aiogram 3.29.0 and makes the entire bot layer async. The layered architecture is preserved; only the Telegram integration and dependency set change.

**Async execution model:**

- All bot-layer functions (`app/bot/`) are `async def`.
- Sync DB and I/O calls are wrapped with `asyncio.to_thread(fn, *args)`.
- The search context store (`app/bot/context.py`) uses `asyncio.Lock` for thread-safe async access.
- Spotify token/cache state uses a reentrant lock (`threading.RLock`) for sync callers inside `to_thread`.

**Routing:**

```text
aiogram Dispatcher
 ├── handlers_router   → @router.message(Command(...)) and @router.message(F.text)
 └── callbacks_router  → @router.callback_query() (manual data-string dispatch)
```

Command handlers are registered before the `F.text` catch-all within `handlers_router`, so aiogram matches them in the correct order.

**Startup sequence (`app/main.py`):**

```python
dp.include_router(handlers_router)
dp.include_router(callbacks_router)
await bot.delete_webhook(drop_pending_updates=True)
await dp.start_polling(bot)
```

**Removed dependencies:**

- `pyTelegramBotAPI` — replaced by `aiogram 3.29.0`
- `deezer-python` — Deezer search now uses `httpx` directly in `deezer_service.py`
- `lyricsgenius` — lyrics fetching now uses `httpx` with the Genius search API directly
- `requests` — no remaining direct usage; `httpx` covers all HTTP needs

**Database and schema unchanged in v3.0.0:** SQLite file format, schema, and all repository function signatures are identical to v2.7.0. No migration needed for the aiogram upgrade.

## v3.1.0 PostgreSQL Migration

Version `v3.1.0` replaces SQLite with PostgreSQL (asyncpg) as the persistence layer.

**Connection pool lifecycle (schema setup superseded by v3.1.1 — see below):**

```python
# startup — app/main.py
await init_db_pool()     # creates the connection pool

# shutdown — app/main.py finally block
await close_db_pool()    # drains pool and resets singleton
```

At v3.1.0, `init_db_pool()` also ran `create_tables_pg`, `create_indexes_pg`, and
`record_schema_version_pg` against a fresh connection from the pool. As of v3.1.1, schema setup
moved to Alembic and `init_db_pool()` only creates the pool — see "v3.1.1 Alembic Migration
Tooling" below. The pool itself is still a module-level singleton in `app/database/db.py`; all
repository modules call `get_pool()` to acquire a connection.

**Type changes from SQLite to PostgreSQL:**

| SQLite                              | PostgreSQL              |
|-------------------------------------|-------------------------|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` |
| `INTEGER` (Telegram IDs, FK cols)   | `BIGINT`                |
| `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | `TIMESTAMPTZ DEFAULT NOW()` |

**Test isolation:**

Tests run against a real PostgreSQL instance via `testcontainers` (postgres:16). The `live_pg`
fixture in `tests/conftest.py` creates a function-scoped asyncpg pool, runs DDL, TRUNCATEs all
tables, and monkeypatches `get_pool` in every repository module before each test.

**async execution model (v3.1.0+):**

- All database calls are natively async — no `asyncio.to_thread` wrappers remain.
- Repository functions use `async with pool.acquire() as conn` for per-call connection checkout.
- The Spotify token/cache state remains `threading.RLock`-protected for the sync callers in the platform layer.

**Data migration:**

`scripts/migrate_sqlite_to_postgres.py` is a one-time standalone script that:
1. Opens the SQLite file read-only.
2. Built the PG schema via `create_tables_pg` + `create_indexes_pg` at v3.1.0 — as of v3.1.1,
   this step runs `alembic upgrade head` instead (see "v3.1.1 Alembic Migration Tooling" below).
3. Migrates tables in FK-safe order (`schema_migrations → users → tracks → searches → favorites → errors`), preserving explicit `id` values.
4. Resets each BIGSERIAL sequence with `SELECT setval(pg_get_serial_sequence(...))` after bulk insert.
5. Verifies row counts and exits non-zero on mismatch.
6. Aborts if target tables are non-empty (pass `--force` to override).

## v3.1.1 Alembic Migration Tooling

Version `v3.1.1` replaces the hand-built schema-migration mechanism (`create_tables_pg`,
`create_indexes_pg`, `migrate_db`/`add_column_if_missing`) with Alembic, the industry-standard
migration tool. The app runtime stays on asyncpg — Alembic is used with raw SQL migrations only
(`op.execute(...)` inside revision files); no SQLAlchemy ORM/Core models describe the schema.

**Schema ownership:**

- `migrations/versions/` is the single source of truth for the database schema. The baseline
  revision (`bf5069cbb1be`) mirrors what `create_tables_pg` + `create_indexes_pg` used to create,
  verified identical via direct structural comparison (`information_schema`/`\d+` diff) before
  being adopted.
- `app/database/schema.py`, `indexes.py`, and `migrations.py` are retired and deleted.
- `init_db_pool()` (`app/database/db.py`) now only creates the asyncpg connection pool — it makes
  no schema assumptions beyond "the schema already exists."

**Deploy-time schema setup:**

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && python run.py"]
```

The container entrypoint (`deploy/Dockerfile`) runs `alembic upgrade head` before the bot starts.
This is idempotent — a no-op once already at head — so it is safe on every container start or
restart.

**Test isolation:**

The `live_pg` fixture (`tests/conftest.py`) builds the test schema once per session via
`alembic upgrade head` (the `pg_schema` fixture), instead of calling `create_tables_pg`/
`create_indexes_pg` directly. Functional equivalence was proven by running the full `*_pg.py`
test suite unchanged against the Alembic-built schema.

**Adopting the existing live database:**

The schema in the existing production database was already identical to the Alembic baseline
(verified via structural comparison against a fresh database built by `alembic upgrade head`).
It was adopted non-destructively with `alembic stamp head`, which writes only a tracking row
into a new `alembic_version` table — it runs no DDL and never touches existing data.

**Schema version reporting:**

`get_schema_version()` (`app/database/maintenance.py`) now returns the running app version
directly — see "Schema Version Visibility" above.

**Data migration script:**

`scripts/migrate_sqlite_to_postgres.py` now bootstraps its target schema via
`alembic upgrade head` (the programmatic API, run synchronously before the async migration logic
starts — Alembic's async template calls `asyncio.run()` internally, which cannot nest inside an
already-running event loop) instead of calling `create_tables_pg`/`create_indexes_pg` directly.
