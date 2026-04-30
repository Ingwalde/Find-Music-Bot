# Changelog

All notable changes to this project will be documented in this file.

---

## [v1.6.0] - 2026-04-28

### Added
- Added SQLite indexes for common queries.
- Added `updated_at` field for cached tracks.
- Added cached track lookup by Deezer ID.
- Added `MAX_HISTORY_PER_USER` environment variable.
- Added automatic search history trimming.

### Changed
- Track card opening now checks SQLite cache before calling Deezer API.
- Favorites can open cached track metadata faster.
- Search history storage is limited to prevent unlimited database growth.
- README updated to `v1.6.0`.
- Bot version updated to `v1.6.0`.

### Fixed
- Reduced unnecessary Deezer API requests for already cached tracks.
- Improved local database performance for users, tracks, searches, favorites and errors.

---

## [v1.5.0] - 2026-04-28

### Added
- Added `app/bot/constants.py` for shared button texts and callback prefixes.
- Added `app/bot/actions.py` for shared bot actions.
- Added feature-based callback modules.
- Added feature-based keyboard modules.

### Changed
- Refactored `callbacks.py` into a lightweight callback router.
- Refactored `keyboards.py` into a compatibility import module.
- Moved shared actions out of `handlers.py`.
- Reduced duplicated callback strings and menu labels.

### Removed
- `app/bot/states.py` is no longer needed and should be removed from the project.

---

## [v1.4.0] - 2026-04-27

### Added
- Added file logging to `logs/bot.log`.
- Added admin-only `/errors` command.
- Added admin-only `/clear_errors` command.
- Added SQLite error history reader.
- Added centralized error logging helper.

---

## [v1.3.0] - 2026-04-27

### Added
- Added track release date to track cards.
- Added Deezer rank to track cards.
- Added user-friendly popularity label based on Deezer rank.
- Added SQLite fields for `release_date`, `rank`, and `popularity`.

---

## [v1.2.0] - 2026-04-27

### Added
- Added Back to results button.
- Improved history menu.
- Improved favorites menu.

---

## [v1.1.0] - 2026-04-26

### Added
- Added search results pagination.
- Added improved search history.
- Added search mode with Main menu button.

---

## [v1.0.0] - 2026-04-26

### Added
- Initial Deezer-based music search.
- Track cards with album cover.
- Deezer button.
- Genius lyrics page lookup.
- Favorites and search history.
- SQLite database.
