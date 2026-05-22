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

## Planned

### v2.6.0 — Admin UX & Operational Polish Update

- Better formatting for admin reports
- Safer confirmation flow for cleanup commands
- Optional `/admin` menu command
- More focused admin/help documentation

### v3.0.0 — Production Architecture Update

- Optional FastAPI admin API
- Optional deployment target documentation
- Better production monitoring structure
- Optional PostgreSQL-ready configuration

## Not Planned for v2.x

- Additional music platforms
- Web dashboard
- Complex production orchestration
- Full PostgreSQL migration


## Admin access configuration

Admin menu visibility is controlled by local admin IDs from `config/admins.json` or the legacy `ADMIN_ID` environment variable. `config/admins.json` must stay local and is ignored by Git.
