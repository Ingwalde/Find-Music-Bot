# Changelog

All notable changes to this project will be documented in this file.

---

## [v1.9.0] - 2026-04-30

### Added
- Added multi-language interface support.
- Added English as default and fallback language.
- Added Ukrainian language support.
- Added Norwegian language support.
- Added German language support.
- Added French language support.
- Added Spanish language support.
- Added Italian language support.
- Added Polish language support.
- Added `/language` command.
- Added language selection keyboard.
- Added `app/localization/` package.
- Added user language storage in SQLite.
- Added language migration for existing local databases.

### Changed
- Bot messages are now loaded through localization keys.
- Main menu buttons are generated based on selected language.
- History and favorites menus support selected language.
- Track action buttons support selected language.
- Callback data remains language-independent.

### Notes
English is used as the default fallback language if a translation is missing.

---

## [v1.8.0] - 2026-04-28

### Added
- Added improved GitHub-ready README structure.
- Added `docs/ARCHITECTURE.md`.
- Added `docs/ROADMAP.md`.
- Added `docs/RELEASE_WORKFLOW.md`.
- Added `screenshots/README.md`.

---

## [v1.7.0] - 2026-04-28

### Added
- Added pytest test suite.

---

## [v1.6.0] - 2026-04-28

### Added
- Added SQLite indexes.
- Added cached track lookup by Deezer ID.
- Added automatic search history trimming.

---

## [v1.5.0] - 2026-04-28

### Added
- Added feature-based callback modules.
- Added feature-based keyboard modules.

---

## [v1.4.0] - 2026-04-27

### Added
- Added file logging.
- Added admin-only error commands.

---

## [v1.3.0] - 2026-04-27

### Added
- Added release date and popularity/rank.

---

## [v1.2.0] - 2026-04-27

### Added
- Added Back to results.
- Improved history and favorites.

---

## [v1.1.0] - 2026-04-26

### Added
- Added pagination.

---

## [v1.0.0] - 2026-04-26

### Added
- Initial Deezer MVP.
