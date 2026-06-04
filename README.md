# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)

**Current version:** `v2.5.2 — Small Cleanup & Runtime Polish Update`

Telegram Music Finder Bot is a Python Telegram bot for searching music, showing track information, saving favorites, viewing search history, opening lyrics pages, and providing admin maintenance tools.

The project is built as a backend-style portfolio project with modular architecture, SQLite persistence, external API integrations, localization, logging, automated tests, coverage reports, Ruff checks, GitHub Actions, Docker support, release cleanup checks, admin diagnostics, database maintenance tools, and versioned releases.

---

## Main Features

### Music Search

- Search tracks by title, artist, or free-text query.
- Uses Deezer as the main music data source.
- Shows paginated search results.
- Keeps temporary search context for pagination and track selection.
- Automatically cleans expired in-memory search contexts.

### Track Cards

Each selected track can show:

- Track title.
- Artist name.
- Album title.
- Duration.
- Release date when available.
- Popularity/rank label when available.
- Deezer track link.
- Cover image when available.
- Spotify link when available.
- Genius lyrics link when available.

### Platform Links

- Deezer is the primary search source.
- Spotify enrichment is optional and controlled by environment variables.
- Spotify failures do not break the main Deezer-based result flow.
- Spotify 403 responses trigger a temporary cooldown to avoid repeated failed lookups.
- Genius lyrics lookup is optional and disabled safely when `GENIUS_TOKEN` is not configured.

### Favorites

- Add tracks to favorites.
- Remove tracks from favorites.
- View saved favorites.
- Clear favorites with confirmation.
- Favorite state is stored in SQLite.

### Search History

- Save user search queries.
- View recent search history.
- Re-run searches from history.
- Clear search history with confirmation.
- Search history is stored in SQLite and can be trimmed by maintenance tools.

### Localization

- Main menu and bot actions support multiple languages.
- Supported language set includes English, Ukrainian, Norwegian, German, French, Spanish, Italian, and Polish.
- English is the baseline language.
- Missing translation keys fall back to English.
- Locale coverage can be checked with a helper script.

### Admin Menu

Admin users can get an extra admin button in the main menu.

Admin access can be configured through:

- `ADMIN_ID` in `.env`.
- local `config/admins.json` based on `config/admins.example.json`.

The local `config/admins.json` file is ignored by Git and should not be committed.

Admin menu actions include:

- Statistics report.
- Maintenance report.
- Health report.
- Cleanup saved errors.
- Cleanup search history.
- Reload admin configuration cache.

Slash commands are also kept as fallback admin access:

```text
/errors           Show recent saved errors
/clear_errors     Clear saved errors
/health           Show runtime health checks
/stats            Show users/searches/favorites/tracks/errors statistics
/maintenance      Show database size, schema version and maintenance status
/cleanup_errors   Keep newest saved errors and remove older rows
/cleanup_history  Keep newest search history rows per user and remove older rows
```

### Admin Diagnostics

Admin diagnostics include:

- Bot version.
- Database status.
- Database path.
- Database size.
- Table counts.
- Schema version.
- Spotify availability/cooldown status.
- Genius configuration status.
- Recent saved errors.

### Database and Persistence

The project uses SQLite for local persistence.

Stored data includes:

- Users.
- Tracks.
- Favorites.
- Search history.
- Spotify cached links.
- Error history.
- Schema migration version.

Database features:

- Schema initialization.
- Lightweight migrations.
- Index creation.
- Repository modules split by domain.
- Compatibility repository facade for stable imports.
- Database maintenance helpers.
- Dynamic maintenance table discovery from SQLite schema.

### Error Logging

- Runtime errors can be saved into the database.
- Error logging is designed not to crash the bot if the database is unavailable.
- Admins can inspect and clear saved errors.

### Testing and Quality

The project includes automated quality checks:

- Pytest test suite.
- Coverage reporting through `pytest-cov`.
- Minimum coverage gate.
- Ruff linting.
- GitHub Actions workflow.
- Release cleanup validation script.
- Locale coverage checker.

Useful commands:

```bash
python -m ruff check .
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
```

### Docker Support

Docker files are stored in `deploy/`.

Build image:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

Run with Docker Compose:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Run in background:

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

Stop:

```bash
docker compose -f deploy/docker-compose.yml down
```

Docker Compose mounts:

- `data/` to persist SQLite database.
- `logs/` to persist logs.
- `config/` as read-only config for admin IDs.

---

## Tech Stack

- Python
- pyTelegramBotAPI
- Deezer Python API client
- Spotify Web API
- Genius / lyricsgenius
- SQLite
- pytest
- pytest-cov
- Ruff
- GitHub Actions
- Docker
- Docker Compose

---

## Project Structure

```text
app/
├── bot/                 # Telegram handlers, callbacks, keyboards and user flows
├── config/              # Environment settings and admin access config
├── database/            # SQLite schema, migrations, indexes, maintenance and repositories
├── localization/        # Translations, languages and fallback translator
├── platforms/           # Platform integrations, Spotify modules and aggregator
├── services/            # Deezer, lyrics, formatting and platform service facades
├── utils/               # Logging, text and time helpers
├── admin_tools.py       # Admin statistics, maintenance and cleanup reports
├── health.py            # Admin health diagnostics
├── main.py              # Bot startup
└── version.py           # Project version

config/
└── admins.example.json  # Public admin config template

deploy/
├── Dockerfile           # Container image definition
└── docker-compose.yml   # Local Docker Compose startup

docs/                    # Architecture, deployment, roadmap and release workflow docs
requirements/
├── base.txt             # Production dependencies
└── dev.txt              # Development and test dependencies
scripts/                 # Release, cleanup and quality helper scripts
tests/                   # Automated tests
.github/workflows/       # GitHub Actions CI
```

---

## Setup

### 1. Clone repository

```bash
git clone https://github.com/Ingwalde/Find-Music-Bot.git
cd Find-Music-Bot
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

Production dependencies:

```bash
python -m pip install -r requirements/base.txt
```

Development dependencies:

```bash
python -m pip install -r requirements/dev.txt
```

### 4. Create `.env`

Copy `.env.example` to `.env` and fill in your tokens.

Windows:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Required:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

Optional:

```env
GENIUS_TOKEN=your_genius_token_here
SPOTIFY_ENABLED=true
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_MARKET=NO
ADMIN_ID=your_telegram_user_id
DATABASE_PATH=data/music_bot.db
LOG_FILE_PATH=logs/bot.log
LOG_LEVEL=INFO
```

### 5. Configure local admin IDs

Copy the example file:

```bash
copy config\admins.example.json config\admins.json
```

Linux/macOS:

```bash
cp config/admins.example.json config/admins.json
```

Example:

```json
{
  "admin_ids": [123456789]
}
```

`config/admins.json` is local-only and should not be committed.

---

## Running Locally

```bash
python run.py
```

Expected log:

```text
Bot started successfully.
```

---

## Running with Docker

Build image:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

Start with Compose:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Start in background:

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

View logs:

```bash
docker compose -f deploy/docker-compose.yml logs -f
```

Stop:

```bash
docker compose -f deploy/docker-compose.yml down
```

---

## Development Checks

Run before committing:

```bash
python -m ruff check .
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
python -c "from app.version import __version__; print(__version__)"
```

Docker check:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

---

## Release Safety

Do not commit or upload local/private files:

```text
.env
config/admins.json
.git/
data/
logs/
.pytest_cache/
.ruff_cache/
.vscode/
__pycache__/
coverage.xml
.coverage
*.pyc
*.zip
```

Use this check before release:

```bash
python scripts/check_release_clean.py
```

Avoid sharing raw `docker compose config` output because it can expose secrets from `.env`.

---

## Roadmap

Planned next stages:

```text
v2.5.2 - Small Cleanup & Runtime Polish Update
v2.6.0 - Structural Refactor Update
v3.0.0 - aiogram Migration
```

---

## Notes

This project is intended as a portfolio backend/bot project. It focuses on practical Telegram bot functionality, API integration, local persistence, maintainability, testing, Docker deployment and production-style cleanup practices.
