# Roadmap

## Completed

- `v1.0.0` — Deezer MVP
- `v1.1.0` — Pagination and History Update
- `v1.2.0` — UX Improvements
- `v1.3.0` — Track Metadata Update
- `v1.4.0` — Logging Update
- `v1.5.0` — Project Refactoring Update
- `v1.6.0` — Database Optimization Update
- `v1.7.0` — Tests Update
- `v1.8.0` — GitHub Polish Update
- `v1.9.0` — Multi-Language Update
- `v2.0.0` — Spotify API Integration
- `v2.1.0` — Architecture Cleanup Update
- `v2.2.0` — Stability, Testing & GitHub CI Update
- `v2.2.1` — GitHub Actions Runtime Update
- `v2.3.0` — Docker & Deployment Update
- `v2.4.0` — Quality, Coverage & Release Cleanup Update
- `v2.4.1` — Coverage Expansion Update
- `v2.5.0` — Database Maintenance & Admin Tools Update
- `v2.5.1` — Stability & Architecture Cleanup Update

## Planned

### v2.5.2 — Small Project Cleanup Update

- Clean up small compatibility/facade leftovers where safe
- Improve root/docs organization without changing runtime behavior
- Review partially translated locale keys and document fallback behavior
- Add small tests for cleanup edge cases

### v2.6.0 — Bot Structure Refactor Update

- Split bot handlers, callbacks and keyboards into packages
- Organize tests by domain folders
- Keep compatibility facades during the transition
- Reduce remaining large modules without changing bot behavior

### v3.0.0 — Aiogram Migration Update

- Migrate from pyTelegramBotAPI to aiogram 3.x
- Move Telegram handling to async architecture
- Rework routing, middleware and state handling
- Revisit long-term production deployment options after async migration

## Not Planned for v2.x

- Additional music platforms
- Web dashboard
- Complex production orchestration
- Full PostgreSQL migration


## Admin access configuration

Admin menu visibility is controlled by local admin IDs from `config/admins.json` or the legacy `ADMIN_ID` environment variable. `config/admins.json` must stay local and is ignored by Git.


### v2.5.1 follow-up
- Admin language UX fixes: admin button remains visible after language changes and admin menu buttons use localized labels.
