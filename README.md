# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)

**Current version:** `v2.5.1 — Stability & Architecture Cleanup Update`

Telegram Music Finder Bot is a Python Telegram bot for finding music through Deezer, opening Spotify links when available, saving favorite tracks, viewing search history and opening Genius lyrics pages.

The project is built as a backend-style portfolio project: modular architecture, SQLite persistence, external API integrations, localization, logging, tests, coverage reports, Ruff checks, GitHub Actions, Docker support, release cleanup checks, admin diagnostics, database maintenance tools and versioned GitHub releases.

---

## Features

- Search tracks using Deezer.
- Show track title, artist, album, duration, release date and popularity label.
- Open Deezer track links.
- Optionally enrich tracks with Spotify links.
- Open Genius lyrics pages.
- Save and remove favorite tracks.
- View and clear search history.
- Multi-language menu support.
- Admin error log commands.
- Admin health-check command.
- Admin statistics command.
- Admin maintenance report command.
- Admin cleanup commands for saved errors and search history.
- Admin button in the main menu for users listed in `config/admins.json`.
- SQLite database with migrations, indexes and schema version visibility.
- Automated tests and coverage gate.
- Ruff code quality checks.
- Release cleanup validation for private/local files.
- GitHub Actions workflow.
- Docker and Docker Compose support.

---


## What Changed in v2.5.1

- Cached admin ID loading from `config/admins.json` to avoid reading/parsing JSON on every message.
- Localized the Genius lyrics URL button through the existing translation system.
- Added a thread-safe Spotify runtime lock for token/cache/cooldown state.
- Added TTL-based cleanup for in-memory search contexts to avoid unbounded memory growth.
- Removed the lazy `actions.py → handlers.py` import workaround by registering the music search handler explicitly.
- Updated database maintenance table reporting to discover tables from SQLite schema instead of a hardcoded list.
- Added tests for admin cache behavior, search context expiration, dynamic maintenance table discovery, localized Genius button and Spotify runtime lock behavior.
- Updated project version to `2.5.1`.

This release is based on the external code review notes and focuses on stability, thread-safety and small architecture cleanup. It does not add new music platforms.

---

## What Changed in v2.5.0

- Added database maintenance utilities.
- Added database size, table counts and schema version reporting.
- Added admin `/stats` command.
- Added admin `/maintenance` command.
- Added admin `/cleanup_errors` command.
- Added admin `/cleanup_history` command.
- Added admin menu button visibility based on `config/admins.json`.
- Added schema version tracking through `schema_migrations`.
- Added tests for admin reports, database maintenance helpers and admin handlers.
- Updated project version to `2.5.0`.

This release focuses on admin diagnostics and long-term database maintenance. It does not add new music platforms.

---

## What Changed in v2.4.1

- Expanded the test suite from 169 to 196 tests.
- Increased full-project coverage from 85% to 93.40%.
- Added additional tests for runtime startup, database repositories, Deezer service and Spotify auth/client behavior.
- Added and verified a minimum coverage gate of 85%.

---

## What Changed in v2.4.0

- Added pytest coverage reporting through `pytest-cov`.
- Added coverage configuration to `pyproject.toml`.
- Added `scripts/check_release_clean.py` to detect tracked local/private files before release.
- Added release cleanup validation to GitHub Actions.
- Updated `.gitignore` and `.dockerignore` for coverage artifacts and local archives.
- Updated project version to `2.4.0`.

This release focuses on code quality, CI confidence and clean release packaging. It does not add new music platforms or change the main bot behavior.

---

## What Changed in v2.3.0

- Added `Dockerfile` for containerized bot startup.
- Added `docker-compose.yml` for one-command local Docker run.
- Added `.dockerignore` to keep local/private files out of Docker builds.
- Added `docs/DEPLOYMENT.md` with local, Docker and Docker Compose instructions.
- Added Docker build validation to GitHub Actions.
- Added GitHub Actions badge to README.
- Updated `.env.example` with clearer environment variable descriptions.
- Updated project version to `2.3.0`.

This release focuses on deployment readiness. It does not add new music platforms or change the main bot behavior.

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

---

## Project Structure

```text
app/
├── bot/                 # Telegram handlers, callbacks and keyboards
├── config/              # Environment-based settings
├── database/            # SQLite schema, migrations, indexes, maintenance and repositories
├── localization/        # Translations and language support
├── platforms/           # Platform integrations, Spotify modules and aggregator
├── services/            # Deezer, Spotify, lyrics and formatting services
├── utils/               # Logging, text and time helpers
├── admin_tools.py       # Admin statistics, maintenance and cleanup reports
├── health.py            # Admin health diagnostics
├── main.py              # Bot startup
└── version.py           # Project version

tests/                   # Automated tests
scripts/                 # Release cleanup scripts
docs/                    # Architecture, roadmap, deployment and release workflow
.github/workflows/       # GitHub Actions CI
Dockerfile               # Container image definition
docker-compose.yml       # Local Docker Compose startup
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

```bash
python -m pip install -r requirements.txt
```

For development tools:

```bash
python -m pip install -r requirements-dev.txt
```

### 4. Create `.env`

Copy `.env.example` to `.env` and fill in your tokens:

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
ADMIN_ID=your_telegram_user_id
```

---

## Admin Commands

Admin-only actions can be enabled either through `ADMIN_ID` in `.env` or through a local `config/admins.json` file. The local `config/admins.json` file is ignored by Git; use `config/admins.example.json` as a template.

```json
{
  "admin_ids": [123456789]
}
```

Admin tools are available from the extra 🛠 Admin button in the main menu for allowed users. Slash commands are also kept as fallback.

```text
/errors           Show recent saved errors
/clear_errors     Clear saved errors
/health           Show runtime health checks
/stats            Show users/searches/favorites/tracks/errors statistics
/maintenance      Show database size, schema version and maintenance status
/cleanup_errors   Keep newest saved errors and remove older rows
/cleanup_history  Keep newest search history rows per user and remove older rows
```

---

## Run Bot Locally

```bash
python run.py
```

---

## Run with Docker

Build the image:

```bash
docker build -t telegram-music-finder-bot .
```

Run with Docker Compose:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

More details are available in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## Run Tests

Install development tools first:

```bash
python -m pip install -r requirements-dev.txt
```

Run Ruff and tests with coverage:

```bash
python -m ruff check .
python -m pytest
```

Show missing coverage lines in the terminal:

```bash
python -m pytest --cov=app --cov-report=term-missing
```

---

## Quality Checks

Current validation target:

```text
Ruff: passed
Pytest: 196+ tests
Coverage gate: 85%
Latest measured coverage: 93%+ in v2.5.1
Release cleanup check: enabled
Docker build: checked in GitHub Actions
```

Before release, verify that private/local files are not tracked:

```bash
python scripts/check_release_clean.py
git ls-files .env data logs .pytest_cache .ruff_cache .vscode coverage.xml .coverage
```

---

## License

This project is intended for portfolio and educational use.
