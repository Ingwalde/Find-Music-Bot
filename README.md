# Telegram Music Finder Bot

Telegram Music Finder Bot is a Python Telegram bot for discovering songs through Deezer.

Users can search for songs, view track metadata, open Deezer links, save favorite tracks, remove tracks from favorites, use paginated search results, return back to search results, repeat searches from history, and open lyrics pages on Genius.

## Current Version

**v1.5.0 — Project Refactoring Update**

Latest updates:
- Split large callback logic into feature-based modules
- Split keyboard builders into smaller files
- Added centralized button and callback constants
- Added shared bot actions module
- Removed duplicated callback strings and menu labels
- Prepared project structure for future platform integrations

## Features

- Search tracks by song name
- Paginated search results with Prev / Next buttons
- Back to results button from a track card
- Show title, artist, album, duration, release date and popularity
- Show album cover from Deezer
- Deezer URL button instead of long link in message
- Inline buttons for track selection
- Add tracks to favorites
- Remove tracks from favorites
- Improved favorites list
- Clear favorites with confirmation
- Improved search history with clickable previous queries
- Clear search history with confirmation
- Genius lyrics page lookup
- SQLite database
- Environment-based configuration
- File logging to `logs/bot.log`
- SQLite error history
- Admin-only error commands
- Refactored project structure for maintainability

## Tech Stack

- Python
- pyTelegramBotAPI
- Deezer API via deezer-python
- LyricsGenius
- SQLite
- python-dotenv

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
│
└── app/
    ├── main.py
    ├── version.py
    ├── config/
    ├── bot/
    │   ├── actions.py
    │   ├── constants.py
    │   ├── handlers.py
    │   ├── callbacks.py
    │   ├── track_callbacks.py
    │   ├── pagination_callbacks.py
    │   ├── favorites_callbacks.py
    │   ├── history_callbacks.py
    │   ├── lyrics_callbacks.py
    │   ├── keyboard_menus.py
    │   ├── keyboard_search.py
    │   ├── keyboard_track.py
    │   ├── keyboard_favorites.py
    │   ├── keyboard_history.py
    │   ├── keyboards.py
    │   ├── messages.py
    │   └── context.py
    ├── services/
    ├── database/
    └── utils/
```

## Installation

```bash
git clone https://github.com/yourusername/telegram-music-finder-bot.git
cd telegram-music-finder-bot
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token_here
GENIUS_TOKEN=your_genius_token_here

DATABASE_PATH=data/music_bot.db
MAX_SEARCH_RESULTS=30
RESULTS_PER_PAGE=5
HISTORY_LIMIT=10

LOG_LEVEL=INFO
LOG_FILE_PATH=logs/bot.log
ERROR_HISTORY_LIMIT=10
ADMIN_ID=your_telegram_user_id
```

## Run

```bash
python run.py
```

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

## Roadmap

- [x] Deezer search
- [x] Album cover
- [x] Deezer button
- [x] Favorites
- [x] Remove from favorites
- [x] Search history
- [x] Pagination
- [x] Back to results
- [x] Improved history
- [x] Improved favorites
- [x] Release date
- [x] Popularity / rank
- [x] File logging
- [x] Admin error commands
- [x] Project refactoring
- [ ] Database optimization
- [ ] Tests
- [ ] Screenshots
- [ ] YouTube / YouTube Music buttons
- [ ] Apple Music button
- [ ] Spotify integration
- [ ] Docker
- [ ] Deployment guide

