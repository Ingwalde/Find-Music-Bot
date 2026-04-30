# Roadmap

This roadmap describes planned development after `v1.8.0`.

## Completed

### v1.0.0 — Deezer MVP

- Deezer track search
- Track cards
- Album covers
- Deezer button
- Genius lyrics link
- Favorites
- Search history
- SQLite database

### v1.1.0 — Pagination and History Update

- Search results pagination
- Prev / Next buttons
- Improved search history
- Search mode with Main menu button

### v1.2.0 — UX Improvements

- Back to results
- Improved history menu
- Improved favorites menu
- Clear confirmations

### v1.3.0 — Track Metadata Update

- Release date
- Deezer rank
- User-friendly popularity labels
- Metadata stored in SQLite

### v1.4.0 — Logging Update

- File logging
- SQLite error history
- Admin-only `/errors`
- Admin-only `/clear_errors`

### v1.5.0 — Project Refactoring Update

- Split callback logic
- Split keyboard builders
- Added constants
- Added shared actions module

### v1.6.0 — Database Optimization Update

- SQLite indexes
- Track cache lookup
- `updated_at` for tracks
- Search history trimming

### v1.7.0 — Tests Update

- pytest setup
- tests for utilities
- tests for Deezer formatting
- tests for pagination context
- tests for keyboard builders
- tests for SQLite repositories

### v1.8.0 — GitHub Polish Update

- improved README
- architecture docs
- roadmap docs
- release workflow docs
- screenshots guide

## Planned

### v1.9.0 — Multi-Language Update

- Add interface language selection
- Add Ukrainian language support
- Add Norwegian language support
- Add German language support
- Add French language support
- Add Spanish language support
- Add Italian language support
- Add Polish language support
- Store selected user language in SQLite
- Add `/language` command
- Add language selection keyboard
- Translate bot messages, buttons and menu texts

Supported languages:

```text
🇺🇦 Ukrainian
🇳🇴 Norwegian
🇩🇪 German
🇫🇷 French
🇪🇸 Spanish
🇮🇹 Italian
🇵🇱 Polish

### v2.0.0 — Spotify API Integration

- Spotify API integration
- Spotify Developer App setup
- Spotify Client Credentials Flow
- Spotify token caching
- Exact Spotify track search by title and artist
- Spotify button in track card
- New `.env` variables:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`