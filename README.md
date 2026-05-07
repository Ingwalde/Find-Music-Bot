# Telegram Music Finder Bot

## Current Version

**v2.1.0 — Architecture Cleanup Update**

This release improves the internal project structure after the large Spotify API integration.

## What Changed

- Database schema, migrations and indexes are split into separate modules.
- Database repositories are split by domain.
- Localization is split into `translator.py` and separate locale files.
- Spotify integration is split into platform modules: auth, matcher and client.
- Compatibility facades keep old imports working.

## Important

This update does not add major user-facing features. It focuses on maintainability and cleaner architecture.

## New Structure Highlights

```text
app/database/
├── db.py
├── schema.py
├── migrations.py
├── indexes.py
└── repository_modules/
    ├── users.py
    ├── searches.py
    ├── tracks.py
    ├── favorites.py
    ├── errors.py
    └── spotify.py

app/localization/
├── translator.py
└── locales/
    ├── en.py
    ├── uk.py
    ├── no.py
    ├── de.py
    ├── fr.py
    ├── es.py
    ├── it.py
    └── pl.py

app/platforms/
├── aggregator.py
└── spotify/
    ├── auth.py
    ├── client.py
    └── matcher.py
```

## Run

```bash
python run.py
```

## Run Tests

```bash
python -m pytest
```

## GitHub Safety

Do not publish local/private files:

```text
.env
data/
logs/
.git/
__pycache__/
.pytest_cache/
.vscode/
```
