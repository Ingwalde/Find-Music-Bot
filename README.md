# Telegram Music Finder Bot

**Current version:** `v2.2.0 — Stability, Testing & GitHub CI Update`

Telegram Music Finder Bot is a Python Telegram bot for finding music through Deezer, opening Spotify links when available, saving favorite tracks, viewing search history and opening Genius lyrics pages.

The project is built as a backend-style portfolio project: modular architecture, SQLite persistence, external API integrations, localization, logging, tests and versioned GitHub releases.

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
- GitHub Actions test workflow.

---

## What Changed in v2.2.0

- Added GitHub Actions workflow for automated tests.
- Added `pyproject.toml` for pytest and Ruff configuration.
- Added `requirements-dev.txt` for development tooling.
- Added admin `/health` command.
- Added `app/health.py` for bot, database and integration diagnostics.
- Improved Deezer error handling so external API failures do not crash normal search flow.
- Improved Spotify fallback tests.
- Fixed duplicated `admin_only` response in `/errors` handler.
- Updated version, changelog, roadmap and release workflow documentation.

---

## Tech Stack

- Python
- pyTelegramBotAPI
- Deezer Python API client
- Spotify Web API
- Genius / lyricsgenius
- SQLite
- pytest
- GitHub Actions

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
docs/                    # Architecture, roadmap and release workflow
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

```bash
pip install -r requirements.txt
```

For development tools:

```bash
pip install -r requirements-dev.txt
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

## Run Bot

```bash
python run.py
```

---

## Run Tests

```bash
python -m pytest
```

With development tools installed:

```bash
ruff check .
python -m pytest
```

---

## Admin Commands

```text
/errors       Show recent saved errors
/clear_errors Clear saved errors
/health       Show bot, database and integration diagnostics
/version      Show current version
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
.vscode/
```

If `.env` was committed or uploaded anywhere, regenerate Telegram, Genius and Spotify credentials.
