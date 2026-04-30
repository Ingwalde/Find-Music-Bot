# Telegram Music Finder Bot

Telegram Music Finder Bot is a Python Telegram bot for discovering songs through Deezer.

Users can search for songs, view track metadata, open Deezer links, save favorite tracks, remove tracks from favorites, use paginated search results, return back to search results, repeat searches from history, and open lyrics pages on Genius.

## Current Version

**v1.7.0 — Tests Update**

Latest updates:
- Added pytest test suite
- Added tests for utility functions
- Added tests for track card formatting
- Added tests for Deezer data normalization
- Added tests for pagination/search context
- Added tests for keyboard builders
- Added tests for SQLite repository logic
- Added isolated temporary SQLite database for tests

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
- Cached track metadata
- Environment-based configuration
- File logging to `logs/bot.log`
- SQLite error history
- Admin-only error commands
- Refactored project structure for maintainability
- Automated tests with pytest

## Tech Stack

- Python
- pyTelegramBotAPI
- Deezer API via deezer-python
- LyricsGenius
- SQLite
- python-dotenv
- pytest

## Environment Variables

Create `.env` file:

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

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

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
- [x] Database optimization
- [x] Tests
- [ ] Screenshots
- [ ] YouTube / YouTube Music buttons
- [ ] Apple Music button
- [ ] Spotify integration
- [ ] Docker
- [ ] Deployment guide

## License

MIT
