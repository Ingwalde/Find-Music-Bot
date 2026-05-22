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
requirements-dev.txt
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
Dockerfile
docker-compose.yml
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
