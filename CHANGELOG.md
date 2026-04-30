# Changelog

All notable changes to this project will be documented in this file.

---

## [v1.5.0] - 2026-04-28

### Added
- Added `app/bot/constants.py` for shared button texts and callback prefixes.
- Added `app/bot/actions.py` for shared bot actions.
- Added feature-based callback modules:
  - `track_callbacks.py`
  - `pagination_callbacks.py`
  - `favorites_callbacks.py`
  - `history_callbacks.py`
  - `lyrics_callbacks.py`
- Added feature-based keyboard modules:
  - `keyboard_menus.py`
  - `keyboard_search.py`
  - `keyboard_track.py`
  - `keyboard_favorites.py`
  - `keyboard_history.py`

### Changed
- Refactored `callbacks.py` into a lightweight callback router.
- Refactored `keyboards.py` into a compatibility import module.
- Moved shared actions out of `handlers.py`.
- Reduced duplicated callback strings and menu labels.
- Updated README to `v1.5.0`.
- Updated bot version to `v1.5.0`.

### Removed
- `app/bot/states.py` is no longer needed and should be removed from the project.

### Notes
This release focuses on internal project structure and maintainability. It does not significantly change the Telegram user experience.

---

## [v1.4.0] - 2026-04-27

### Added
- Added file logging to `logs/bot.log`.
- Added configurable logging settings:
  - `LOG_LEVEL`
  - `LOG_FILE_PATH`
  - `ERROR_HISTORY_LIMIT`
  - `ADMIN_ID`
- Added admin-only `/errors` command.
- Added admin-only `/clear_errors` command.
- Added SQLite error history reader.
- Added centralized error logging helper.

### Changed
- Errors are now logged to console and file.
- Important runtime errors are also saved to SQLite.
- Updated bot version to `v1.4.0`.

### Fixed
- Main menu button placement is kept as a bottom keyboard in history and favorites screens.

---

## [v1.3.0] - 2026-04-27

### Added
- Added track release date to track cards.
- Added Deezer rank to track cards.
- Added user-friendly popularity label based on Deezer rank.
- Added SQLite fields for `release_date`, `rank`, and `popularity`.
- Added simple SQLite migration for old local databases.

### Changed
- Improved track metadata formatting.
- Updated saved favorite tracks to preserve release date and popularity data.

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
