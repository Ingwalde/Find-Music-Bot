# Architecture

This document explains the internal structure of Telegram Music Finder Bot.

## High-Level Flow

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
 ↓
SQLite Database
```

## Main Layers

### 1. Entry Point

```text
run.py
```

Starts the application by calling `run_bot()` from `app/main.py`.

### 2. Main Application

```text
app/main.py
```

Responsible for:

- loading settings
- initializing SQLite database
- creating the Telegram bot instance
- registering handlers
- registering callback handlers
- starting polling

### 3. Bot Layer

```text
app/bot/
```

Contains Telegram-specific logic.

Important files:

```text
handlers.py              → message commands and text handling
callbacks.py             → callback router
actions.py               → shared bot actions
constants.py             → button names and callback prefixes
messages.py              → reusable bot messages
context.py               → in-memory search pagination context
```

Callback logic is split by feature:

```text
track_callbacks.py       → track card opening
pagination_callbacks.py  → page navigation and back to results
favorites_callbacks.py   → add/remove/clear favorites
history_callbacks.py     → repeat/clear search history
lyrics_callbacks.py      → Genius lyrics page lookup
```

Keyboard builders are split by feature:

```text
keyboard_menus.py
keyboard_search.py
keyboard_track.py
keyboard_favorites.py
keyboard_history.py
keyboards.py
```

`keyboards.py` works as a compatibility module that re-exports keyboard builders.

### 4. Service Layer

```text
app/services/
```

Contains integrations and formatting logic.

```text
deezer_service.py        → Deezer search and track normalization
lyrics_service.py        → Genius lyrics page lookup
track_formatter.py       → Telegram track card formatting
```

### 5. Database Layer

```text
app/database/
```

Contains SQLite setup and repository functions.

```text
db.py                    → table creation, migrations, indexes
repositories.py          → users, searches, tracks, favorites, errors
```

Database tables:

```text
users
searches
tracks
favorites
errors
```

### 6. Utility Layer

```text
app/utils/
```

Contains reusable helpers.

```text
logger.py                → console/file logging
error_logger.py          → log and save errors
text.py                  → text formatting helpers
time.py                  → duration formatting
```

## Data Flow: Search

```text
User sends song name
 ↓
handlers.py
 ↓
actions.send_search_results()
 ↓
deezer_service.search_tracks()
 ↓
context.save_search_context()
 ↓
repositories.save_search()
 ↓
search_results_keyboard()
 ↓
Telegram inline results
```

## Data Flow: Open Track Card

```text
User clicks track button
 ↓
callbacks.py router
 ↓
track_callbacks.py
 ↓
SQLite cache lookup
 ↓
Deezer fallback if not cached
 ↓
repositories.save_track()
 ↓
actions.send_track_card()
 ↓
track_formatter.format_track_card()
 ↓
Telegram track card
```

## Data Flow: Favorites

```text
User clicks Add to favorites
 ↓
favorites_callbacks.py
 ↓
repositories.add_favorite()
 ↓
SQLite favorites table
 ↓
inline keyboard updates
```

## Database Optimization

Starting from `v1.6.0`, the bot uses:

- SQLite indexes
- cached track lookup by Deezer ID
- `updated_at` field for tracks
- search history trimming through `MAX_HISTORY_PER_USER`

This reduces unnecessary Deezer API calls and keeps the local database cleaner.

## Testing

Starting from `v1.7.0`, the project includes tests for:

- utility functions
- text formatting
- track card formatting
- Deezer object normalization
- pagination context
- keyboard builders
- SQLite repositories
