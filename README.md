# Telegram Music Finder Bot

Telegram Music Finder Bot is a Python Telegram bot for discovering songs through Deezer.

The bot allows users to search for tracks, view track cards with album covers and metadata, open Deezer links, save favorite tracks, reuse search history, choose interface language, and open Genius lyrics pages.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Deezer](https://img.shields.io/badge/API-Deezer-purple)
![Tests](https://img.shields.io/badge/Tests-pytest-green)

## Current Version

**v1.9.0 — Multi-Language Update**

Latest updates:
- Added multi-language interface support
- Added `/language` command
- Added language selection keyboard
- Added English as default/fallback language
- Added Ukrainian, Norwegian, German, French, Spanish, Italian and Polish interface support
- Added user language storage in SQLite
- Added localization layer for bot messages and visible buttons

## Supported Languages

```text
🇬🇧 English
🇺🇦 Ukrainian
🇳🇴 Norwegian
🇩🇪 German
🇫🇷 French
🇪🇸 Spanish
🇮🇹 Italian
🇵🇱 Polish
```

## Features

- Search tracks by song name through Deezer
- Paginated search results with Prev / Next buttons
- Back to results button from track cards
- Track cards with title, artist, album, duration, release date, popularity and album cover
- Deezer URL as a clean inline button
- Add and remove favorite tracks
- Improved favorites list
- Clickable search history
- Genius lyrics page lookup
- Multi-language interface
- SQLite database with cached track metadata
- File logging to `logs/bot.log`
- Admin-only error commands
- Automated tests with pytest

## Bot Commands

```text
/start - Start bot
/help - Show help
/language - Change language
/version - Show bot version
/favorites - Show favorite tracks
/history - Show search history
/errors - Show recent saved errors (admin only)
/clear_errors - Clear saved errors (admin only)
```

## Run

```bash
python run.py
```

## Run Tests

```bash
python -m pytest
```

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
- [x] Multi-language interface
- [ ] Spotify API integration
- [ ] Multi-platform search links
- [ ] Docker
- [ ] Deployment guide
- [ ] CI / GitHub Actions

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

## License

MIT
