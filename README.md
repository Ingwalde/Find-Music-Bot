# Telegram Music Finder Bot

## Current Version

**v2.0.1 — Spotify Stability Patch**

This patch improves the Spotify API integration added in `v2.0.0`.

## What changed

- Spotify `403 Forbidden` is now handled more clearly.
- Spotify lookups are temporarily paused after access errors to avoid repeated warnings and delays.
- Added `SPOTIFY_ENABLED` toggle.
- Added `SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS` setting.
- Improved Spotify search query fallback.
- Added Spotify troubleshooting documentation.

## Spotify Environment Variables

```env
SPOTIFY_ENABLED=true
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_MARKET=NO
SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS=3600
```

If Spotify returns `403 Forbidden`, the bot will continue working with Deezer only and will skip Spotify requests for the cooldown period.

## Track Card Buttons

When Spotify is available:

```text
[🎧 Deezer] [🟢 Spotify]
[⬅️ Back to results]
[📖 Lyrics] [⭐ Add to favorites]
[🔎 Search again]
```

When Spotify is unavailable:

```text
[🎧 Deezer]
[⬅️ Back to results]
[📖 Lyrics] [⭐ Add to favorites]
[🔎 Search again]
```

## Troubleshooting

See: [`docs/SPOTIFY_TROUBLESHOOTING.md`](docs/SPOTIFY_TROUBLESHOOTING.md)

## Run

```bash
python run.py
```

## Run Tests

```bash
python -m pytest
```
