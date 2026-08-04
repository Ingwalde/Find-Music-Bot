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
- `v2.5.2` — Small Cleanup & Runtime Polish Update
- `v2.6.0` — Smart Recommendations Update
- `v2.6.1` — Localization & Error Logging Fixes Update
- `v2.7.0` — Bot Structure Refactor Update
- `v3.0.0` — aiogram Migration Update
- `v3.0.1` — Async Event-Loop Hygiene Patch
- `v3.1.0` — PostgreSQL Migration
- `v3.1.1` — Alembic Migration Tooling
- `v3.1.2` — Rate Limiting, Retry Logic, Log Rotation & Search Cache

## Current admin/runtime foundation

- Admin menu visibility is controlled by local admin IDs from `config/admins.json` or the legacy `ADMIN_ID` environment variable.
- `config/admins.json` must stay local and is ignored by Git.
- Admin language UX fixes are included: the admin button remains visible after language changes and admin menu buttons use localized labels.
- v3.0.0 completes the async migration to aiogram 3.x. Deezer and lyrics integrations use httpx directly.
- v3.1.0 completes the PostgreSQL migration. All database access is natively async via asyncpg. SQLite has been removed. Docker compose includes the Postgres service with healthcheck.
- v3.1.1 replaces the hand-built schema-migration mechanism with Alembic. Schema is owned by `migrations/versions/`; the container entrypoint runs `alembic upgrade head` before the bot starts.
- v3.1.2 adds per-user rate limiting, automatic retry on transient external-API failures, daily log rotation, and a PostgreSQL-backed search result cache (24h TTL) — the first schema change applied through a new Alembic revision since v3.1.1 took ownership.

- `v3.3.3` — Documentation Fixes
- `v3.4.0` — Observability (JSON logging, correlation ID, Prometheus metrics)
- `v3.4.1` — Graceful Resilience (SIGTERM drain, breaker half-open state)
- `v3.4.2` — Test Depth (property-based tests, concurrency/race scenarios)

## Planned
- `v3.5.0` — Admin Audit & Rate Limit Hardening

## Not Planned for v3.x

- Additional music platforms.
- Web dashboard.
- Complex production orchestration.
