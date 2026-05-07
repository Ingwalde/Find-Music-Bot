# Architecture

## Overview

The bot is split into layers:

```text
Telegram Bot Layer
 ↓
Bot Actions / Callback Router
 ↓
Services / Platform Aggregator
 ↓
Database Repositories
 ↓
SQLite
```

## Bot Layer

```text
app/bot/
```

Contains Telegram handlers, callbacks and keyboard builders.

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
db.py           → connection and init_db()
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
