# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)

**Current version:** `v2.4.1 — Coverage Expansion Update`

Telegram Music Finder Bot is a Python Telegram bot for finding music through Deezer, opening Spotify links when available, saving favorite tracks, viewing search history and opening Genius lyrics pages.

The project is built as a backend-style portfolio project: modular architecture, SQLite persistence, external API integrations, localization, logging, tests, coverage reports, Ruff checks, GitHub Actions, Docker support, release cleanup checks and versioned GitHub releases.

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
- SQLite database with migrations and indexes.
- Automated tests.
- Test coverage reporting with pytest-cov.
- Ruff code quality checks.
- Release cleanup validation for private/local files.
- GitHub Actions workflow.
- Docker and Docker Compose support.

---

## What Changed in v2.4.1

- Expanded coverage-focused tests for runtime startup, database repositories, Deezer service and Spotify client/auth modules.
- Increased test coverage beyond the v2.4.0 baseline.
- Updated project version to `2.4.1`.
- Kept release notes in GitHub Releases and version history in `CHANGELOG.md`.

This patch release focuses only on test coverage and quality confidence. It does not change user-facing bot behavior.

---

## What Changed in v2.4.0

- Added pytest coverage reporting through `pytest-cov`.
- Added coverage configuration to `pyproject.toml`.
- Added `scripts/check_release_clean.py` to detect tracked local/private files before release.
- Added release cleanup validation to GitHub Actions.
- Updated `.gitignore` and `.dockerignore` for coverage artifacts and local archives.
- Updated project version to `2.4.0`.
- Expanded the test suite and introduced an 85% coverage baseline.

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

## What Changed in v2.2.1

- Updated GitHub Actions workflow to use Node.js 24-compatible action versions.
- Updated `actions/checkout` from `v4` to `v6`.
- Updated `actions/setup-python` from `v5` to `v6`.
- Added pip dependency caching in CI.
- Added Ruff check step to the GitHub Actions workflow.
- Updated project version to `2.2.1`.
- Confirmed local quality checks: Ruff passed and 66 tests passed.

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
├── database/            # SQLite schema, migrations, indexes and repositories
├── localization/        # Translations and language support
├── platforms/           # Platform integrations, Spotify modules and aggregator
├── services/            # Deezer, Spotify, lyrics and formatting services
├── utils/               # Logging, text and time helpers
├── health.py            # Admin health diagnostics
├── main.py              # Bot startup
└── version.py           # Project version

tests/                   # Automated tests
scripts/                 # Release cleanup and maintenance scripts
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
Pytest: 66 tests passed
Coverage: generated by pytest-cov
Release cleanup check: enabled
Docker build: checked in GitHub Actions
```

Before release, verify that private/local files are not tracked:

```bash
python scripts/check_release_clean.py
```

---

## Admin Commands

```text
/errors        Show recent saved errors
/clear_errors  Clear saved errors
/health        Show bot, database and integration diagnostics
/version       Show current version
```

`/errors`, `/clear_errors` and `/health` require `ADMIN_ID` in `.env`.

---

## GitHub Safety

Do not publish local/private files:

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

If `.env` was committed or uploaded anywhere, regenerate Telegram, Genius and Spotify credentials.
