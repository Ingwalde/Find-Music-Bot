# Changelog

All notable changes to this project will be documented in this file.

---

## [v2.1.0] - 2026-04-30

### Added
- Added `app/database/schema.py`.
- Added `app/database/migrations.py`.
- Added `app/database/indexes.py`.
- Added split repository modules under `app/database/repository_modules/`.
- Added split localization files under `app/localization/locales/`.
- Added `app/localization/translator.py`.
- Added platform layer under `app/platforms/`.
- Added Spotify platform modules:
  - `app/platforms/spotify/auth.py`
  - `app/platforms/spotify/client.py`
  - `app/platforms/spotify/matcher.py`
- Added `app/platforms/aggregator.py`.
- Added architecture import tests.

### Changed
- `app/database/db.py` now coordinates schema, migrations and indexes instead of containing everything.
- `app/database/repositories.py` is now a compatibility facade.
- `app/database/spotify_repository.py` is now a compatibility facade.
- `app/localization/translations.py` is now a compatibility facade.
- `app/services/spotify_service.py` is now a compatibility facade.
- `app/services/track_platform_service.py` is now a compatibility facade.
- Improved project maintainability after Spotify API integration.

### Notes
This release does not add major user-facing features. It focuses on internal architecture and long-term maintainability.
