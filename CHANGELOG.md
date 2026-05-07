# Changelog

All notable changes to this project will be documented in this file.

---

## [v2.0.1] - 2026-04-30

### Added
- Added `SPOTIFY_ENABLED` environment toggle.
- Added `SPOTIFY_FORBIDDEN_COOLDOWN_SECONDS` setting.
- Added Spotify access cooldown after `403 Forbidden` responses.
- Added clearer Spotify access error handling.
- Added broad Spotify search fallback query.
- Added `docs/SPOTIFY_TROUBLESHOOTING.md`.
- Added tests for Spotify query building and temporary access block state.

### Changed
- Spotify lookup no longer repeatedly calls the API after access is forbidden.
- Spotify errors are now handled as optional integration errors, not bot-breaking errors.
- README updated to `v2.0.1`.
- Bot version updated to `v2.0.1`.

### Notes
If Spotify credentials are missing, invalid, or restricted, the bot continues working with Deezer only.

---

## [v2.0.0] - 2026-04-30

### Added
- Added Spotify Web API integration.
- Added Spotify Client Credentials Flow.
- Added Spotify access token caching.
- Added Spotify track search by title and artist.
- Added Spotify button to track cards.
- Added Spotify metadata cache in SQLite.
- Added `spotify_track_id`, `spotify_link`, and `spotify_updated_at` fields to `tracks`.
- Added `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_MARKET` environment variables.
- Added tests for Spotify service helpers.
