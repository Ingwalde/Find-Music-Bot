# Telegram Music Finder Bot

Telegram Music Finder Bot is a Python Telegram bot for discovering songs through Deezer.

Users can search for songs, view track metadata, open Deezer links, save favorite tracks, remove tracks from favorites, check search history and open lyrics pages on Genius.

## Features

- Search tracks by song name
- Show title, artist, album and duration
- Show album cover from Deezer
- Deezer URL button instead of long link in message
- Inline buttons for track selection
- Add tracks to favorites
- Remove tracks from favorites
- Show favorite tracks
- Show search history
- Genius lyrics page lookup
- SQLite database
- Environment-based configuration
- Clean project structure for GitHub

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
│
└── app/
    ├── main.py
    ├── config/
    ├── bot/
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

Create `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token_here
GENIUS_TOKEN=your_genius_token_here

DATABASE_PATH=data/music_bot.db
MAX_SEARCH_RESULTS=10
```

`GENIUS_TOKEN` is optional for the main Deezer search. If it is missing, lyrics lookup will be disabled.

## Run

```bash
python run.py
```

## Bot Commands

```text
/start - Start bot
/help - Show help
/favorites - Show favorite tracks
/history - Show search history
```

## Current Version

### v1.0.0 — Deezer MVP

- Deezer track search
- Track cards with album covers
- Deezer button
- Favorites
- Remove from favorites
- Search history
- Genius lyrics page button
- SQLite database

## Roadmap

- [x] Deezer search
- [x] Inline result buttons
- [x] Track details
- [x] Album cover
- [x] Deezer button
- [x] Favorites
- [x] Remove from favorites
- [x] Search history
- [x] Genius lyrics page lookup
- [ ] Pagination
- [ ] Better favorites management
- [ ] YouTube / YouTube Music search buttons
- [ ] Apple Music search button
- [ ] Spotify integration
- [ ] Admin statistics
- [ ] Docker support
- [ ] Tests
- [ ] Deployment guide

## Security Notes

If a Telegram bot token was exposed, revoke it in BotFather and generate a new one.

## License

MIT
