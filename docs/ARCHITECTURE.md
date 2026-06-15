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
SQLite
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
schema.py       → CREATE TABLE statements
migrations.py   → lightweight SQLite migrations
indexes.py      → CREATE INDEX statements
db.py           → connection, init_db() and schema version recording
maintenance.py  → database size, table counts, cleanup helpers and schema version visibility
```

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

Version `v2.5.0` adds a lightweight `schema_migrations` table.

It records application schema versions during `init_db()` and allows the admin `/maintenance` command to show the current schema version.

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
- SQLite database connectivity;
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
data/ -> SQLite database
logs/ -> runtime logs
```

Docker Compose uses `.env` for configuration and mounts `data/` and `logs/` as local volumes.

---

## Quality and Release Safety

```text
scripts/
└── check_release_clean.py   # Validates that private/local files are not tracked by Git
```

The cleanup script checks tracked files only. This allows developers to keep local `.env`, logs and SQLite files in the working directory while preventing them from being committed or released.


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
