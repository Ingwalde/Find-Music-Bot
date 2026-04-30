# Telegram Music Finder Bot

Telegram Music Finder Bot is a Python Telegram bot for discovering songs through Deezer.

The bot allows users to search for tracks, view track cards with album covers and metadata, open Deezer links, save favorite tracks, reuse search history, and open Genius lyrics pages.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Deezer](https://img.shields.io/badge/API-Deezer-purple)
![Tests](https://img.shields.io/badge/Tests-pytest-green)

## Current Version

**v1.8.0 — GitHub Polish Update**

Latest updates:
- Improved README structure for portfolio presentation
- Added architecture documentation
- Added roadmap documentation
- Added release workflow documentation
- Added screenshots guide
- Improved GitHub project presentation
- Updated changelog and version file

## Features

- Search tracks by song name through Deezer
- Paginated search results with Prev / Next buttons
- Back to results button from track cards
- Track cards with:
  - title
  - artist
  - album
  - duration
  - release date
  - popularity / Deezer rank
  - album cover
- Deezer URL as a clean inline button
- Add tracks to favorites
- Remove tracks from favorites
- Improved favorites list
- Clear favorites with confirmation
- Improved search history with clickable previous queries
- Clear search history with confirmation
- Genius lyrics page lookup
- SQLite database
- Cached track metadata
- File logging to `logs/bot.log`
- Admin-only error commands
- Automated tests with pytest
- Refactored project structure

## Tech Stack

- Python
- pyTelegramBotAPI
- Deezer API via deezer-python
- LyricsGenius
- SQLite
- python-dotenv
- pytest

## Project Structure

```text
telegram-music-finder-bot/
│
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── CHANGELOG.md
├── pytest.ini
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── RELEASE_WORKFLOW.md
│
├── screenshots/
│   └── README.md
│
├── tests/
│   ├── test_time.py
│   ├── test_text.py
│   ├── test_track_formatter.py
│   ├── test_deezer_service.py
│   ├── test_context.py
│   ├── test_keyboards.py
│   └── test_repositories.py
│
└── app/
    ├── main.py
    ├── version.py
    ├── config/
    ├── bot/
    ├── services/
    ├── database/
    └── utils/
```

## Architecture

```text
User
 ↓
Telegram Bot
 ↓
Message Handlers / Callback Router
 ↓
Bot Actions
 ↓
Services
 ├── Deezer Service
 ├── Genius Service
 └── Track Formatter
 ↓
SQLite Database
 ├── Users
 ├── Searches
 ├── Tracks
 ├── Favorites
 └── Errors
```

More details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/telegram-music-finder-bot.git
cd telegram-music-finder-bot
```

Create virtual environment:

```bash
python -m venv venv
```

Activate it.

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create `.env` file from `.env.example`:

```env
BOT_TOKEN=your_telegram_bot_token_here
GENIUS_TOKEN=your_genius_token_here

DATABASE_PATH=data/music_bot.db
MAX_SEARCH_RESULTS=30
RESULTS_PER_PAGE=5
HISTORY_LIMIT=10
MAX_HISTORY_PER_USER=100

LOG_LEVEL=INFO
LOG_FILE_PATH=logs/bot.log
ERROR_HISTORY_LIMIT=10
ADMIN_ID=your_telegram_user_id
```

## Run

```bash
python run.py
```

## Run Tests

```bash
python -m pytest
```

The test suite uses a temporary SQLite database and does not call real Deezer, Genius or Telegram APIs.

## Bot Commands

```text
/start - Start bot
/help - Show help
/version - Show bot version
/favorites - Show favorite tracks
/history - Show search history
/errors - Show recent saved errors (admin only)
/clear_errors - Clear saved errors (admin only)
```

## Screenshots

Screenshots are not included with tokens or private data.

Recommended screenshots:

```text
screenshots/start.png
screenshots/search-results.png
screenshots/track-card.png
screenshots/favorites.png
screenshots/history.png
screenshots/errors-admin.png
```

Guide: [`screenshots/README.md`](screenshots/README.md)

## Roadmap

See full roadmap: [`docs/ROADMAP.md`](docs/ROADMAP.md)

Short version:

- [x] Deezer search
- [x] Album cover
- [x] Favorites
- [x] Search history
- [x] Pagination
- [x] Back to results
- [x] Release date and popularity
- [x] Logging
- [x] Tests
- [x] Database optimization
- [x] GitHub documentation polish
- [ ] Screenshots
- [ ] YouTube / YouTube Music buttons
- [ ] Apple Music button
- [ ] Spotify integration
- [ ] Docker
- [ ] Deployment guide

## GitHub Safety

Do not publish local/private files:

```text
.env
data/
logs/
.git/
__pycache__/
.vscode/
```

Use `.env.example` for public configuration examples.

## Release Workflow

See: [`docs/RELEASE_WORKFLOW.md`](docs/RELEASE_WORKFLOW.md)

## License

MIT
