# Changelog

All notable changes to this project will be documented in this file.

---

## [v3.7.8] - 2026-08-15

### Added
- **Redis-backed search context** — `app/bot/context.py` now stores paginated search
  results in Redis (`sc:{user_id}`, 1h TTL via `SETEX`) so pagination survives a bot
  restart. Falls back to the existing in-memory dict when Redis is unavailable.
- **Redis tier for the search cache** — `app/services/search_cache_service.py` checks
  Redis before PostgreSQL and warms Redis on a PostgreSQL hit. The PostgreSQL tier is
  kept, not replaced: a Redis outage or eviction costs latency, never a cold cache.
- **Trivy image scan** — `.github/workflows/tests.yml` scans the built image for
  HIGH/CRITICAL vulnerabilities and fails the build on fixable findings.
  `ignore-unfixed: true` so unpatched base-image CVEs do not block every PR.
- **`scripts/check_version_sync.py`** — fails when `app/version.py` and the newest
  CHANGELOG entry disagree.
- **`.github/workflows/sync-deps-branch.yml`** — daily job keeping the `deps/staging`
  branch merged up with `main`, opening an issue on conflict.
- **`LOG_SAMPLE_RATE`** setting (default `1.0`, no change in behaviour) — samples out a
  fraction of DEBUG/INFO records under high traffic. WARNING and above, and any record
  carrying exception info, are never sampled.
- Healthchecks on the `test-postgres` and `test-redis` compose services, so
  `docker compose up -d --wait` blocks until both actually accept connections.

### Changed
- **Dependabot now targets `deps/staging`** instead of `main`, so dependency PRs no
  longer land directly against the release branch.
- **Multi-stage `deploy/Dockerfile`** — pip and the wheels it downloads stay in the
  build stage. Measured: 368 MB → 347 MB (-21 MB).
- **mypy strict coverage 11 → 25 modules** — all `repository_modules/`, plus
  `app/bot/context.py`, `app/config/settings.py`, `app/services/search_cache_service.py`,
  and `app/utils/http_retry.py`. The checked set now lives in `[tool.mypy] files` in
  `pyproject.toml`, so CI runs a bare `python -m mypy` and cannot drift from that list.
- Dependency bumps: `alembic` 1.18.5 → 1.19.1, `ruff` 0.16.1 → 0.16.2,
  `mypy` >=1.14.0 → >=2.3.0, `hypothesis` >=6.165.2, `pip-audit` >=2.10.1,
  `docker/setup-buildx-action` v3 → v4, `docker/login-action` v3 → v4,
  `docker/build-push-action` v6 → v7, `appleboy/ssh-action` 1.2.0 → 1.2.5,
  `appleboy/scp-action` 0.1.7 → 1.0.0.
- `docs/ARCHITECTURE.md` — added a layer-to-module table so each box in the diagram
  maps to concrete files.

### Fixed
- **`app/version.py` reported the wrong version to users.** It sat at `3.7.0` from
  v3.7.1 through v3.7.7 — seven releases. `__version__` is read by the `/version`
  command and the admin `/maintenance` report, so both showed a stale version.
  Bumped to `3.7.8` and guarded by the new `check_version_sync.py`.
- **`app/utils/http_retry.py` could raise `None`.** `raise last_error` ran with
  `last_error: Exception | None`; the loop invariant made it non-`None` in practice,
  but a future change to the loop body would have surfaced as a confusing
  "exceptions must derive from BaseException". Now guarded explicitly. Found by
  removing the module's stale `ignore_errors = true` mypy override.

### Notes
- Coverage 95.11% (up from ~94%), 42 new tests covering the Redis paths, their
  fallbacks, and log sampling.
- `LOG_SAMPLE_RATE` defaults to `1.0` — sampling is opt-in and off unless configured.

---

## [v3.7.7] - 2026-08-09

### Added
- **`deploy/grafana-dashboard.json`** — importable Grafana dashboard with 8 panels:
  circuit breaker status, TLS cert expiry gauge, rate limit blocks, request rate by
  service, error rate by service, API latency p50/p95/p99, cache hits vs misses,
  cache hit ratio gauge. Import via Grafana → Dashboards → Import → Upload JSON.

### Changed
- **`.github/workflows/deploy.yml`** — three improvements:
  - Removed docker login/logout (GHCR package is now public — no auth needed to pull).
  - Replaced `git pull origin main` with `actions/checkout` + `appleboy/scp-action`
    copying only `docker-compose.yml` to the server. App code comes from the Docker
    image; the repo clone on the server is no longer a dependency.
  - Removed `envs`/`env` blocks (no credentials passed to server).

### Notes
- No code or schema changes. No user-facing changes.
- Prerequisite: GHCR package `find-music-bot` must be set to Public
  (GitHub → Packages → find-music-bot → Package settings → Change visibility → Public).

---

## [v3.7.6] - 2026-08-09

### Changed
- **`.github/workflows/tests.yml`** — `docker` job now logs in to GHCR and
  pushes `ghcr.io/ingwalde/find-music-bot:latest` on every push to `main`
  (PR runs still build-only). Added `permissions: packages: write`.
- **`docker-compose.yml`** — `music-bot` image changed from `tg-bot` to
  `ghcr.io/ingwalde/find-music-bot:latest`. `build:` kept for local dev.
- **`.github/workflows/deploy.yml`** — three improvements:
  - Trigger changed from `push` to `workflow_run` on `Tests` success —
    deploy only fires after the new image is built and pushed to GHCR.
  - `docker compose pull` + `docker compose up -d` (no `--build`) — server
    pulls the pre-built GHCR image, never builds locally.
  - Post-deploy health check: polls `http://localhost:9090/ready` every 3s
    for up to 60s; on timeout prints last 50 container log lines and exits 1.
  - GHCR login on server via `GITHUB_TOKEN` passed through `envs:`.
  - `command_timeout: 5m`.

### Notes
- No code or schema changes. No user-facing changes.
- First deploy after this merge: GHCR package is created automatically.
  If the package is private by default, go to
  GitHub → Packages → find-music-bot → Package settings → Change visibility → Public.

---

## [v3.7.5] - 2026-08-09

### Added
- **`.github/workflows/deploy.yml`** — automated SSH deploy on every push to `main`:
  `git pull`, `docker compose up -d --build --remove-orphans`, `docker image prune -f`.
  Requires `SSH_HOST`, `SSH_USER`, and `SSH_PRIVATE_KEY` GitHub secrets.
- **`deploy/alerts.yml`** — Prometheus alerting rules: `CircuitBreakerOpen` (>1m),
  `TLSCertExpiringSoon` (<7d), `HighExternalAPIErrorRate` (>10% over 5m),
  `HighRateLimitBlockRate` (>1/s over 10m).

### Notes
- No code or schema changes. No runtime logic changes. No user-facing changes.
- Dependabot was already configured in v3.7.3; no change needed.

---

## [v3.7.4] - 2026-08-09

### Added
- **`app/utils/http_client.py`** — shared `httpx.AsyncClient` singleton following the
  `redis_client.py` init/close/get pattern. `init_http_client()` / `close_http_client()`
  wired into `app/main.py` startup/shutdown. Eliminates per-request client instantiation
  across Deezer, Spotify, and Genius integrations.

### Changed
- **Shared HTTP client** — `async with httpx.AsyncClient(timeout=10)` replaced with
  `get_http_client()` in `app/services/deezer_service.py` (7 call sites),
  `app/services/lyrics_service.py`, `app/platforms/spotify/client.py`,
  `app/platforms/spotify/auth.py`.
- **mypy expanded to 11 modules** — `pyproject.toml` `disallow_untyped_defs = true`
  overrides added for: `app.utils.http_client`, `app.services.lyrics_service`,
  `app.platforms.spotify.client`, `app.services.recommendations_service`,
  `app.bot.rate_limit`, `app.health`, `app.monitoring` (plus existing 4 from v3.7.3).
  CI mypy step updated to cover all 11 files.
- **`app/bot/rate_limit.py`** — Redis helper functions annotated:
  `_check_rate_limit_redis(client: aioredis.Redis, ...)`,
  `_should_warn_once_redis(client: aioredis.Redis, ...)`.

### Notes
- No schema changes. No user-facing changes.
- Fallback in `get_http_client()` preserves test compatibility for tests that mock
  `httpx.AsyncClient` directly.

---

## [v3.7.3] - 2026-08-09

### Added
- **mypy** (`mypy>=1.14.0`) added to `requirements/dev.txt`. Config in `pyproject.toml`:
  `python_version = "3.12"`, `check_untyped_defs = true`. `disallow_untyped_defs = true`
  override on 5 typed modules: `app.utils.types`, `app.services.deezer_service`,
  `app.platforms.aggregator`, `app.services.track_formatter`,
  `app.services.recommendations_service`. `ignore_errors = true` on `app.utils.http_retry`.
- **`pip-audit`** (`pip-audit>=2.7.0`) added to `requirements/dev.txt`. Moved from
  `pip install pip-audit` inline install to dev deps.
- **CI parallelized** — `.github/workflows/tests.yml` split from one sequential job into
  three parallel jobs: `lint` (Ruff, mypy, pip-audit, release/env/locale checks),
  `test` (pytest with PostgreSQL + Redis services), `docker` (Buildx + GHA layer cache).
  Docker build now uses `docker/setup-buildx-action@v3` and `docker/build-push-action@v6`
  with `cache-from: type=gha` / `cache-to: type=gha,mode=max`.
- **Tests for `_check_redis_ready`** — 4 async tests added to `tests/test_monitoring.py`
  covering: no Redis URL configured, client is None, ping succeeds, ping raises.

### Changed
- **`pyproject.toml`** — `target-version = "py310"` → `"py312"` (matches runtime).
  Triggered ruff `UP017` fix: `datetime.timezone.utc` → `datetime.UTC` in
  `app/monitoring.py`, `app/services/recommendations_service.py`,
  `scripts/migrate_sqlite_to_postgres.py`.
- **`README.md`** — restructured for portfolio: "Why this project matters" moved to top,
  removed 15 "What Changed" sections, "What I learned", broken screenshot table, and
  "Notes" section. Added "Changelog" pointer. Added Python 3.12, mypy, hypothesis to
  Tech Stack. Added mypy command to Development Checks.
- **`CHANGELOG.md`** — added missing v3.7.1 and v3.7.2 entries.
- **`docs/ROADMAP.md`** — added v3.7.2 entry.
- **`docs/ROADMAP.md`** — added v3.7.3, v3.7.4, v3.7.5 entries.

### Notes
- No schema changes. No runtime logic changes. No user-facing changes.

---

## [v3.7.2] - 2026-08-05

### Added
- **`app/utils/types.py`** — `TrackDict` TypedDict covering all 13 track dict keys
  (`deezer_track_id`, `title`, `artist`, `album`, `duration`, `duration_seconds`,
  `deezer_link`, `cover_url`, `release_date`, `rank`, `popularity`, `spotify_track_id`,
  `spotify_link`). Used as the structural type for all track dicts across the services layer.
- **`docs/metrics.md`** — complete Prometheus metrics reference: all 8 metrics with types,
  labels, descriptions, scrape config YAML, PromQL query examples, and Grafana panel suggestions.
- **`docs/ARCHITECTURE.md`** — Mermaid flowchart diagram added at the top showing all system
  layers: Telegram API → Bot → Services → Platforms → Database → Infrastructure.

### Changed
- **Type hints** — `list[dict]` → `list[TrackDict]` and `dict` → `TrackDict` in return
  annotations across `app/services/deezer_service.py`, `app/platforms/aggregator.py`,
  `app/services/track_formatter.py`, `app/services/recommendations_service.py`.
- **`README.md`** — added "Why this project matters" and "What I learned" sections;
  preview screenshot table; version updated to v3.7.2.

### Notes
- No schema changes. No runtime logic changes. No user-facing changes.
- TypedDict is `total=False` — structural, no runtime overhead.

---

## [v3.7.1] - 2026-08-05

### Fixed
- **Narrow Redis exception handling** — bare `except Exception` replaced with
  `except (RedisError, OSError)` in both `check_rate_limit` and `should_warn_once`
  (`app/bot/rate_limit.py`) and in the Redis cache read/write paths
  (`app/services/recommendations_service.py`). Prevents swallowing `CancelledError`
  and other non-Redis exceptions. (`from redis.exceptions import RedisError` added.)
- **DB pool creation timeout** — `asyncpg.create_pool()` wrapped in
  `asyncio.wait_for(..., timeout=10.0)` (`app/database/db.py`). Bot now raises
  `asyncio.TimeoutError` instead of hanging indefinitely when PostgreSQL is unreachable
  at startup.
- **Test: `BrokenClient.setex` → `BrokenClient.set`** — `tests/test_redis_trending.py`
  mock used `setex` but production code uses `client.set(key, value, ex=ttl)`. Fixed
  method name to match actual call signature.

### Changed
- **Dependency upper bounds** — `redis>=8.1.0,<9.0.0` and `cryptography>=50.0.0,<52.0.0`
  added to `requirements/base.txt` to prevent silent breakage on next major releases.

### Notes
- No schema changes. No user-facing changes.

---

## [v3.7.0] - 2026-08-04

### Added
- **Redis health checks** — `check_redis()` added to `app/health.py` and surfaced in
  the admin Telegram `/health` command. `/ready` endpoint returns 503 when Redis is
  configured but unreachable (`app/monitoring.py:_check_redis_ready`).
- **Prometheus: `bot_rate_limit_blocked_total`** (Counter) — incremented every time a
  request is blocked by the rate limiter (both in-memory and Redis paths).
  (`app/bot/rate_limit.py`)
- **Prometheus: `bot_tls_cert_expiry_days`** (Gauge) — days until the TLS certificate
  expires, updated on every `/metrics` scrape. Active only when `WEBHOOK_CERT_PATH` is
  set. Returns −1 when the cert file is unreadable. Uses the `cryptography` library
  (`cryptography>=42.0.0` added to `requirements/base.txt`). (`app/monitoring.py`)
- **Startup config log** — on bot start, key non-secret settings are logged at INFO
  level: mode, Redis status, Spotify status, rate-limit parameters, shutdown timeout.
  (`app/main.py:_log_startup_config`)
- **`scripts/check_env_example.py`** — new script: scans all `os.getenv()` calls in
  `app/` and verifies each variable is documented in `.env.example` (active or
  commented-out examples both count). Exits 1 with a list if any are missing.
- **CI step** — `python scripts/check_env_example.py` added to `.github/workflows/tests.yml`.
- **`.env.example`** — added `SHUTDOWN_TIMEOUT_SECONDS`, `RATE_LIMIT_MAX_REQUESTS`,
  `RATE_LIMIT_WINDOW_SECONDS` (were missing since v3.5.0).

### Notes
- No schema changes. No user-facing changes.
- `WEBHOOK_CERT_PATH` already existed; no new env var needed for cert monitoring.

---

## [v3.6.0] - 2026-08-04

### Added
- **Redis integration** — optional Redis backend (`REDIS_URL` env var) for
  stateless rate limiting and trending track cache. Falls back to the existing
  in-memory implementation when Redis is unavailable or not configured.
- **Redis rate limiting** — sliding-window algorithm using a Redis sorted set
  (`ZADD` / `ZREMRANGEBYSCORE` / `ZCARD` pipeline). Admin-exempt flag preserved.
  Warn-once state stored as a Redis key with `NX EX`, cleared on next successful
  request. (`app/bot/rate_limit.py`)
- **Redis trending cache** — trending tracks stored as a JSON blob via `SETEX`
  with a 1-hour TTL. Cache hit serves directly from Redis; miss fetches and
  stores. (`app/services/recommendations_service.py`)
- `app/services/redis_client.py` — `init_redis` / `close_redis` / `get_redis_client`
  helpers. `init_redis` called in `run_bot()` when `REDIS_URL` is set; failure
  is non-fatal (logged as warning, bot continues with in-memory fallback).
- `redis` service added to `docker-compose.yml` (redis:7-alpine, healthcheck);
  `music-bot` depends on it. `test-redis` service added under the `test` profile
  (port 6380) for local integration tests.
- `REDIS_URL` documented in `.env.example`.
- New integration test files: `tests/test_redis_rate_limit.py` (8 tests),
  `tests/test_redis_trending.py` (4 tests). Both require the `test-redis` service
  and use the `live_redis` fixture (added to `tests/conftest.py`).

### Notes
- No schema changes. No breaking changes. No user-facing changes.
- `REDIS_URL` is optional — omit to keep the existing in-memory behaviour.

---

## [v3.5.0] - 2026-08-04

### Added
- **Admin audit log** — every admin action (stats, maintenance, cleanup, health,
  reload admins) is recorded in a new `admin_audit` PostgreSQL table with
  `admin_telegram_id`, `action`, optional `details` (JSONB), and `created_at`.
  New Alembic revision `cf55a191898c`. (`migrations/versions/`,
  `app/database/repository_modules/admin_audit.py`, wired into
  `app/bot/handlers.py:handle_admin_action`)
- `save_admin_audit` / `get_recent_admin_audit` added to the `repositories`
  facade and `__all__`.
- **Rate limit hardening** — `RATE_LIMIT_MAX_REQUESTS` (default 20) and
  `RATE_LIMIT_WINDOW_SECONDS` (default 60) are now configurable via environment
  variables (`app/config/settings.py`). Admin users are unconditionally exempt
  from rate limiting via the new `is_admin` keyword argument to
  `check_rate_limit()` — admins must never be blocked from their own tools.
  All three call sites in `handlers.py` pass the resolved `is_admin` flag.

### Notes
- No user-facing changes for regular users. No breaking changes.
- Schema change: one new Alembic revision. Run `alembic upgrade head` to apply.

---

## [v3.4.2] - 2026-08-04

### Added
- **Property-based tests** — Hypothesis (`hypothesis>=6.100.0`) added to dev
  dependencies. `tests/test_property_based.py` covers six pure functions with
  generated inputs:
  - `convert_duration`: output format, colon count, 2-digit segments, exact
    round-trip for all values 0–359 999 s.
  - `normalize_query`: idempotent, always lowercase, always stripped.
  - `get_popularity_label`: correct label for every rank range, None passthrough.
  - `format_track_card`: supplied title/artist/album always appear in output,
    fallback strings used for missing keys.
  - `truncate_text`: result never exceeds `max_length`; short inputs unchanged.
  - `split_long_message`: every chunk fits; reassembled output equals original.
- **Concurrency test** — `test_concurrent_check_breaker_only_one_probe_wins`
  launches 8 concurrent callers against a half-open breaker and asserts exactly
  one wins the probe slot while the other 7 are blocked.
- **Partial-failure tests** — two new tests in `tests/test_resilience.py` assert
  that HTTP 4xx (client error, immediate raise) and HTTP 5xx (server error,
  exhausted retries) do **not** trip the circuit breaker — only transient network
  errors (`TimeoutException`, `ConnectError`) do.

### Notes
- No production code changes. No schema changes. No breaking changes.

---

## [v3.4.1] - 2026-08-04

### Added
- **Graceful shutdown drain** — `ShutdownMiddleware` tracks the count of in-flight handler
  invocations. `drain_handlers(timeout)` is called in `run_bot()`'s finally block after the
  polling task is cancelled, waiting up to `SHUTDOWN_TIMEOUT_SECONDS` (default 30s, new
  setting) for all handlers to finish before closing the bot session and DB pool. Previously
  a handler awaiting a DB call would receive `CancelledError` mid-flight on SIGTERM.
  (`app/bot/shutdown_middleware.py`)
- **Circuit breaker half-open state** — after the cooldown expires, exactly one probe
  request is allowed through. While that probe is in flight all other callers see the
  breaker as open (fail-fast). If the probe succeeds the breaker fully closes; if it fails
  the cooldown resets. Previously all callers were allowed through simultaneously after
  cooldown expiry. (`app/utils/http_retry.py`)
- `SHUTDOWN_TIMEOUT_SECONDS` setting added to `app/config/settings.py`.

### Notes
- No user-facing changes. No schema changes. No breaking changes.

---

## [v3.4.0] - 2026-08-04

### Added
- **Structured JSON logging** — opt-in via `LOG_FORMAT=json`. When enabled, every log
  record is emitted as a single-line JSON object with `ts`, `level`, `logger`, `message`,
  and `correlation_id` fields, suitable for ingestion by Loki, ELK, or CloudWatch.
  Default remains plain text; no config change means no behavior change.
- **Correlation ID** — each incoming Telegram update is assigned a short random ID
  (12 hex chars) via `CorrelationMiddleware`, stored in a `ContextVar`. In JSON mode the
  ID appears in every log record emitted while that update is being handled, making it
  possible to trace a single interaction across handler → service → platform → database.
  (`app/utils/correlation.py`, `app/bot/correlation_middleware.py`)
- **Prometheus `/metrics` endpoint** — exposed on port 9090 alongside `/health` and
  `/ready`. Scraped by Prometheus, Grafana Agent, VictoriaMetrics, or any compatible
  agent. (`app/monitoring.py`)
- **Instrumentation** — four metrics covering the main operational signals:
  - `bot_external_api_requests_total` (counter, labels: `service`, `outcome`) — total
    requests to Deezer, Spotify, and Genius, labelled `success` or `error`.
  - `bot_external_api_latency_seconds` (histogram, label: `service`) — end-to-end latency
    per top-level retry call (not per attempt).
  - `bot_circuit_breaker_open` (gauge, label: `service`) — 1 when a service's circuit
    breaker is open, 0 otherwise.
  - `bot_search_cache_hits_total` / `bot_search_cache_misses_total` (counters) — PostgreSQL
    search cache hit and miss rate.
  (`app/utils/metrics.py`, wired into `app/utils/http_retry.py` and
  `app/services/search_cache_service.py`)
- `prometheus-client==0.26.0` added to `requirements/base.txt`.
- `LOG_FORMAT` setting added to `app/config/settings.py` (validated: `text` | `json`)
  and documented in `.env.example`.

### Notes
- No user-facing changes. No schema changes. No breaking changes.
- All observability features are additive — the bot's Telegram behavior is identical
  whether or not `LOG_FORMAT=json` is set or a Prometheus scraper is configured.

---

## [v3.3.3] - 2026-08-03

### Fixed
- `README.md`: `DATABASE_URL` is now listed under Required — the bot refuses to start
  without it (`settings.validate()`), but the Setup section previously listed only
  `BOT_TOKEN` and omitted `DATABASE_URL` entirely.
- `README.md`: removed the stale `DATABASE_PATH` line from the "Optional" env block and
  added a note that it is only read by the one-time `scripts/migrate_sqlite_to_postgres.py`
  script — the live database is PostgreSQL.
- `README.md`: "Database features" no longer claims "Schema initialization on first
  startup" and "Index creation" — schema and indexes are owned by Alembic
  (`migrations/versions/`, applied with `alembic upgrade head`) since v3.1.1.
- `README.md`: "Stored data" now names the `alembic_version` table instead of the retired
  hand-built "Schema migration version".
- `README.md`: Docker Support section and Project Structure now show `docker-compose.yml`
  in the project root (moved there in v3.2.0), not under `deploy/`.

### Changed
- `requirements/base.txt`: documented that `sqlalchemy` is present only as an Alembic
  dependency — schema is raw SQL via `op.execute()`, the app runtime uses asyncpg with no
  ORM/Core models.

---

## [v3.3.2] - 2026-07-29

### Added
- Circuit breaker for network-level outages against Spotify, Deezer, and Genius
  (`app/utils/http_retry.py`) — trips after 3 consecutive fully-exhausted calls with a
  pure connection/timeout failure (not HTTP 4xx/5xx), short-circuits further requests to
  that service for `EXTERNAL_SERVICE_COOLDOWN_SECONDS` (default 60s, new setting) instead
  of repeatedly stacking ~90s of retries per call. Per-service state, orthogonal to
  Spotify's existing 403 cooldown.
- Global aiogram error handler (`app/main.py`, registered on `dp.errors`) — logs and
  records any exception that escapes a handler/callback unhandled, via the existing
  admin-visible errors table. Previously such failures were silently dropped with no
  user feedback and no log entry.
- `searching_lyrics` status message is now sent before a Genius lookup and edited in
  place with the result — the translation existed in all 8 locales but was never wired
  up.
- Test coverage for `handle_admin_action` (the admin bottom-menu dispatcher), previously
  untested despite routing all 6 admin report actions.

### Changed
- `callback_router` (`app/bot/callbacks.py`) now guards against malformed/stale
  `callback_data` (missing separator, non-numeric page value) instead of raising past
  the dispatcher.
- `app/database/maintenance.py`: `MAINTENANCE_TABLES` now actually gates
  `get_table_count`'s allowlist (previously only used as a DB-failure fallback); added
  `search_cache` to the list.
- `app/platforms/spotify/auth.py`: the token-fetch lock now covers the whole
  fetch-or-return flow, preventing concurrent callers from duplicating a Spotify token
  request.
- `app/services/recommendations_service.py`: deduplicated the numbered-list formatting
  logic into a shared helper.
- `app/services/lyrics_service.py`: error handling now matches `deezer_service.py`'s
  convention (broader exception handling covering response parsing).
- `app/localization/translator.py`: `t()` now falls back to the unformatted string
  instead of raising when a translation's placeholders don't match the supplied
  arguments.

### Fixed
- Corrected a CHANGELOG ordering mistake: the v3.3.1 entry was listed below v3.3.0
  instead of above it.
- 10 stale "Uses testcontainers" test docstrings updated to describe the compose
  test-postgres service.
- Removed two confirmed-dead functions: `clear_search_context()` and
  `remove_keyboard()`.

### Notes
- No breaking changes. The circuit breaker and global error handler are the only
  behavior changes with real-world effect; both are additive safety nets.

---

## [v3.3.1] - 2026-07-29

### Fixed
- Backfilled the missing v3.1.2 CHANGELOG entry (was documented in `docs/ROADMAP.md` and
  `docs/ARCHITECTURE.md`, never made it into `CHANGELOG.md`).
- Removed the stale `testcontainers` line from README's Tech Stack section (removed from
  `requirements/dev.txt` by the compose-postgres chore, no longer used).
- Replaced README's stale "Roadmap" block (still listed v2.6.1/v3.0.0 as planned; both
  shipped long ago) with a pointer to `docs/ROADMAP.md`.

### Changed
- `.gitignore` now excludes `graphify-out/` (local tooling output, not project source).

### Notes
- Documentation-only patch. No code behavior changes.

---

## [v3.3.0] - 2026-07-28

### Added
- Optional Telegram webhook mode, selected with `BOT_MODE=webhook` (default stays
  `polling` — no config change means no behavior change). Terminates TLS itself with
  a self-signed certificate, listens on port 8443.
- `app/webhook.py` — webhook aiohttp app (`SimpleRequestHandler` with `secret_token`
  validation) and the non-blocking `AppRunner`/`TCPSite` server task.
- `BOT_MODE` and `WEBHOOK_*` settings in `app/config/settings.py`, validated only
  when `BOT_MODE=webhook`.

### Changed
- `app/main.py`'s task wiring now builds `{webhook_task, monitoring_task}` or
  `{polling_task, monitoring_task}` depending on `BOT_MODE` — polling and webhook
  are mutually exclusive at Telegram's API level, monitoring always runs. Same
  `FIRST_COMPLETED`/cancel/shutdown logic as before, generalized over the task set.
- `docker-compose.yml` publishes port 8443 and mounts `./certs` read-only.

### Notes
- No user-facing change; polling remains the default. See docs/DEPLOYMENT.md for
  webhook setup, certificate generation, and required firewall rules.

---

## [v3.2.0] - 2026-06-23

### Added
- HTTP monitoring endpoints via FastAPI alongside the bot's polling: GET /health (liveness)
  and GET /ready (PostgreSQL readiness), port 9090.

### Changed
- `docker-compose.yml` moved from `deploy/` to the project root (plain `docker compose`, no
  `-f`/`--env-file` flags). Dockerfile stays in `deploy/`.
- Dockerfile execs the bot as PID 1 so SIGTERM reaches it (graceful shutdown now works).

### Notes
- No user-facing change; the bot stays on aiogram polling. Endpoints are for Docker
  healthchecks and external uptime monitoring. Webhooks remain a future release.

---

## [v3.1.2] - 2026-06-21

### Added
- Per-user rate limiting (`app/bot/rate_limit.py`) — sliding-window (20 req/60s), in-memory,
  applied to every handler/callback that calls an external API.
- Shared HTTP retry helper (`app/utils/http_retry.py`) for all httpx call sites across
  Deezer, lyrics, and Spotify platform code.
- PostgreSQL-backed search result cache (24h TTL) — `search_cache` table added via a new
  Alembic revision, the first schema change since Alembic took ownership in v3.1.1.

### Changed
- Log rotation switched from size-based to daily rotation (5 days retained).

### Notes
- Backfilled in v3.3.1 — this entry was missing from CHANGELOG.md despite being documented
  as shipped in docs/ROADMAP.md and docs/ARCHITECTURE.md. Date is the real v3.1.2 merge
  commit date, not invented.

---

## [v3.1.1] - 2026-06-19

### Changed
- Replaced the hand-built schema-migration mechanism with Alembic (industry-standard tooling).
  Alembic now owns the database schema; the app runtime stays on asyncpg. Schema is applied via
  `alembic upgrade head` at container start.
- Retired `create_tables_pg`/`create_indexes_pg`/`migrate_db`; `init_db_pool()` now only creates
  the connection pool.
- `get_schema_version()` now returns the app version directly.
- Fixed a facade-rule violation: `aggregator.py` now imports through the `spotify_repository`
  facade.

### Notes
- Backend tooling change, no user-facing effect. Existing data untouched; the live database was
  stamped at the Alembic baseline.

---

## [v3.1.0] - 2026-06-17

### Changed
- Migrated the database from SQLite to PostgreSQL (asyncpg). All database access is now
  fully asynchronous via a connection pool; SQLite code has been removed from the application.
- Repository modules, maintenance layer, error logging, platform aggregator, and health checks
  all operate against PostgreSQL through the shared asyncpg pool.
- `app/main.py` now calls `await init_db_pool()` at startup and `await close_db_pool()` in the
  finally block; the sync `init_db()` call has been removed.
- `asyncio.to_thread` wrappers around database calls removed across the bot layer (handlers,
  callbacks, services) — all DB calls are now natively async.
- `DATABASE_URL` is now required — `settings.validate()` raises `ValueError` if it is missing.

### Added
- PostgreSQL service in `deploy/docker-compose.yml` (postgres:16-alpine) with a `pg_isready`
  healthcheck; bot service depends on `service_healthy`.
- Named volume `postgres-data` for persistent PostgreSQL data.
- `scripts/migrate_sqlite_to_postgres.py` — one-time standalone migration script that reads
  the existing SQLite file (read-only), creates the PG schema, migrates all tables in FK-safe
  order preserving explicit IDs, resets BIGSERIAL sequences, and verifies row counts.

### Notes
- No user-facing feature changes; this is a database backend migration.
- Existing data is preserved via the migration script before switching to PostgreSQL.
- `migrations.py` is kept in place but unreferenced by the application (Stage 12 handles it).
- Tests run against a real PostgreSQL instance via testcontainers.

---

## [v3.0.1] - 2026-06-16

### Changed
- Wrapped two remaining synchronous SQLite calls in `recommendations_service.py` (`get_db_recommendations`, `get_similar_by_genre`) in `asyncio.to_thread` so they no longer briefly block the event loop during recommendation and `/similar` queries.

### Notes
- Internal async hygiene patch — no behavior change for users.
- Test coverage unchanged (312 tests, all passing).

---

## [v3.0.0] - 2026-06-16

### Breaking Changes
- **Migrated from pyTelegramBotAPI to aiogram 3.29.0.** All bot handlers, callbacks, and lifecycle code are now fully async. Any custom fork relying on the sync telebot API must be updated.
- Removed dependencies: `pyTelegramBotAPI`, `deezer-python`, `lyricsgenius`, `requests`.

### Changed
- All bot-layer functions are now `async def` using `asyncio.to_thread` for sync DB/IO calls.
- `app/main.py` now wires `handlers_router` and `callbacks_router` into an aiogram `Dispatcher` and calls `bot.delete_webhook(drop_pending_updates=True)` before polling.
- `app/database/repository_modules/users.py` now imports `User` from `aiogram.types` instead of `telebot.types`.
- Deezer search rewritten with `httpx` (async HTTP, no SDK). Lyrics rewritten with `httpx` direct API. Spotify platform unchanged.

### Fixed
- Fixed track card never reaching the user when a track button was tapped — `send_track_card` in `track_callbacks.py` was called without `await`, silently discarding the coroutine. Caught during aiogram migration smoke testing.

### Notes
- Database schema and SQLite file format unchanged — no migration needed.
- Test coverage remains ≥ 93% (312 tests, all passing).
- All localization keys and 8 supported languages unchanged.

---

## [v2.7.0] - 2026-06-12

### Changed
- Removed unreachable dead-code branches from `process_music_search` (menu-button and `/start` handling, already covered by `text_handler` routing).
- `/similar` and `/trending` now reuse `format_similar_text` and `format_recommendations_text` from `recommendations_service.py` instead of duplicating list-formatting logic. `/similar` output now uses the same grouped `🎤 Artist / 🎵 Others` format as the inline 🎯 Similar button.
- Fixed a `seen_ids` collision in `get_similar_by_genre` where tracks without a `deezer_track_id` could block all related-artist candidates.
- Removed unused compatibility-facade exports from `repositories.py` (`row_to_dict`, `trim_search_history`, `get_table_counts`, `get_schema_version`).
- Extracted `get_user_context()` helper (registers the user and returns their language) used across ~19 handlers.
- Extracted `require_admin()` helper for the 8 admin-only command handlers.
- All repository functions and `init_db()` now close their SQLite connection in a `finally` block, guaranteeing cleanup even if an error occurs.

### Notes
- Internal refactor only — no user-facing feature changes besides the `/similar` formatting unification above.
- Test coverage remains at 93.50% (minimum 85%).

---

## [v2.6.1] - 2026-06-11

### Fixed
- Localized favorites error alerts (were shown in English for all languages)
- Localized version command output
- Added error handling to language selection callback

### Changed
- Track card errors now logged to admin error log (were only logged to file)

### Notes
- Improved test coverage for favorites and history callbacks

---

## [v2.6.0] - 2026-06-09

### Added
- Added `/similar` command — finds tracks similar to the last viewed track using the Deezer radio endpoint (`/track/{id}/radio`).
- Added `/trending` command — shows top tracks of the week via the Deezer chart endpoint (`/chart/0/tracks`).
- Added "You may also like" block sent after each track card based on artist from local DB with fallback to Deezer artist top tracks.
- Added 🎯 Similar inline button on every track card for quick access to similar tracks.
- Added `last_track_id` persistence to the `users` table in SQLite so `/similar` works across sessions.
- Added `get_similar_tracks()`, `get_trending_tracks()`, `get_artist_top_tracks()` to `deezer_service.py`.
- Added `recommendations_service.py` with in-memory trending cache (1-hour TTL) and DB-first recommendation logic.
- Added `similar_callbacks.py` for the 🎯 Similar button callback handler.
- Added `get_tracks_by_artist()` to tracks repository and facade.
- Added `save_last_track_id()` / `get_last_track_id()` to users repository and facade.
- Added localization keys for all 8 languages: `similar_header`, `similar_empty`, `similar_no_context`, `trending_header`, `trending_empty`, `you_may_also_like`, `btn_similar`.
- Updated `/help` command text with new commands in all 8 supported languages.

### Fixed
- Fixed: infinite "menu buttons disabled" loop — users can now open Favorites/History directly while in search mode.
- Removed redundant next-step handler that caused message quote linking in search mode.

### Notes
- Trending results are cached in-memory for 1 hour to reduce Deezer API load.
- "You may also like" queries the local SQLite DB first; Deezer artist API is used as fallback only when no local data is found.
- `last_track_id` is stored in the database so it persists across bot restarts.

---

## [v2.5.2] - 2026-06-04

### Added
- Added lazy Deezer client initialization to avoid import-time client side effects.
- Added lazy Genius client initialization to avoid startup warnings when lyrics are not configured.
- Added thread-safe locking around in-memory search contexts.
- Added localized admin reports and an admin cache reload action.
- Added locale coverage checker script.
- Added `deploy/` and `requirements/` folders for cleaner project layout.

### Changed
- Moved production dependencies to `requirements/base.txt`.
- Moved development dependencies to `requirements/dev.txt`.
- Moved Docker configuration to `deploy/Dockerfile` and `deploy/docker-compose.yml`.
- Updated Docker, setup and development documentation for the new deploy/requirements layout.
- Reworked README into a full project overview instead of a version-by-version release summary.
- Updated project version to `2.5.2`.

### Fixed
- Fixed Ruff `E402` issue in the locale coverage checker.
- Fixed admin report tests after adding localized Spotify status formatting.

### Notes
- The old root `Dockerfile`, `docker-compose.yml`, `requirements.txt`, and `requirements-dev.txt` can be removed after applying this update.
- This release does not add new music platforms.

---

## [v2.5.1] - 2026-05-21

### Added
- Added cached admin ID loading with `clear_admin_ids_cache()` for tests and runtime reload scenarios.
- Added TTL-based cleanup for in-memory search contexts.
- Added dynamic database maintenance table discovery from SQLite schema.
- Added localized `btn_open_genius` translation key for the Genius lyrics URL button.
- Added tests for admin cache behavior, context expiration, dynamic maintenance table discovery, localized Genius button and Spotify runtime lock behavior.
- Added `docs/CODE_REVIEW_ACTION_PLAN.md` to document the review-based improvement roadmap.

### Changed
- Updated project version to `2.5.1`.
- Replaced the lazy `app.bot.handlers` import inside `actions.py` with an explicit music search handler registration.
- Wrapped Spotify token/cache/cooldown runtime state in a reentrant lock for safer threaded handler execution.
- Updated README, roadmap, architecture and release workflow documentation.

### Fixed
- Fixed hardcoded English Genius button text by using the existing localization system.
- Fixed admin button visibility after language switching.
- Fixed admin menu buttons not following the selected language.
- Reduced repeated file I/O by caching admin IDs instead of loading `config/admins.json` on each admin check.
- Reduced risk of unbounded memory growth from stale search pagination contexts.

### Notes
- This patch is based on the external code review findings.
- No new music platforms were added.
- The main bot behavior remains unchanged.

---

## [v2.5.0] - 2026-05-21

### Added
- Added `app/database/maintenance.py` with database size, table counts, schema version and cleanup helpers.
- Added `app/admin_tools.py` with admin statistics, maintenance and cleanup report formatting.
- Added admin `/stats` command.
- Added admin `/maintenance` command.
- Added admin `/cleanup_errors` command.
- Added admin `/cleanup_history` command.
- Added admin menu button visibility based on `config/admins.json`.
- Added admin menu keyboard for stats, maintenance, cleanup and health actions.
- Added `config/admins.example.json` as a safe template for local admin IDs.
- Added `schema_migrations` table for schema version visibility.
- Added tests for database maintenance helpers.
- Added tests for admin reports and admin command handlers.

### Changed
- Updated project version to `2.5.0`.
- Updated README with admin maintenance commands.
- Updated architecture and roadmap documentation for database maintenance.
- Updated release workflow documentation with v2.5 release checks.
- Updated English help text with admin diagnostics commands.
- Updated main menu rendering to show the admin button only for allowed Telegram IDs.

### Notes
- This release focuses on database maintenance and admin tooling.
- No new music platforms were added.
- Main user-facing music search behavior remains unchanged.

---

## [v2.4.1] - 2026-05-21

### Added
- Added additional tests for runtime startup, database repositories, Deezer service and Spotify auth/client behavior.

### Changed
- Updated project version to `2.4.1`.
- Increased full-project coverage from 85% to 93.40%.
- Expanded the test suite from 169 to 196 tests.
- Added and verified a minimum coverage gate of 85%.

### Notes
- This patch release focuses on coverage expansion only.
- Main bot behavior remains unchanged.

---

## [v2.4.0] - 2026-05-19

### Added
- Added pytest coverage reporting through `pytest-cov`.
- Added coverage configuration to `pyproject.toml`.
- Added `scripts/check_release_clean.py` for release safety validation.
- Added release cleanup validation step to GitHub Actions.

### Changed
- Updated project version to `2.4.0`.
- Updated README with coverage and release cleanup instructions.
- Updated release workflow documentation with coverage and cleanup checks.
- Updated roadmap for the v2.4 quality release and v2.5 admin/database maintenance plan.
- Improved `.gitignore` and `.dockerignore` for coverage artifacts and local archives.

### Notes
- This release focuses on code quality, coverage reporting and clean release packaging.
- No new music platforms were added.
- Main bot behavior remains unchanged.

---

## [v2.3.0] - 2026-05-12

### Added
- Added `Dockerfile` for containerized bot startup.
- Added `docker-compose.yml` for one-command local Docker startup.
- Added `.dockerignore` to keep local/private files out of Docker builds.
- Added `docs/DEPLOYMENT.md` with local, Docker and Docker Compose instructions.
- Added Docker build validation step to GitHub Actions.
- Added GitHub Actions badge to README.

### Changed
- Updated project version to `2.3.0`.
- Updated README with Docker usage instructions.
- Updated `.env.example` with clearer configuration descriptions.
- Updated roadmap and release workflow documentation.

### Notes
- This release focuses on deployment readiness.
- No new music platforms were added.
- Main bot behavior remains unchanged.

---

## [v2.2.1] - 2026-05-12

### Changed
- Updated GitHub Actions workflow to use Node.js 24-compatible action versions.
- Updated `actions/checkout` from `v4` to `v6`.
- Updated `actions/setup-python` from `v5` to `v6`.
- Added pip dependency caching to the Python setup step.
- Added Ruff check step to the GitHub Actions workflow.
- Updated project version to `2.2.1`.

### Fixed
- Removed GitHub Actions warning about deprecated Node.js 20 action runtime.
- Ensured CI checks run both Ruff and pytest.

### Notes
- This is a patch release. It does not change bot features or user-facing behavior.

---

## [v2.2.0] - 2026-05-12

### Added
- Added `.github/workflows/tests.yml` for GitHub Actions test automation.
- Added `pyproject.toml` with pytest and Ruff configuration.
- Added `requirements-dev.txt` for development tooling.
- Added `app/health.py` with bot, database, Deezer, Spotify and Genius diagnostics.
- Added admin `/health` command.
- Added tests for health report formatting.
- Added tests for Spotify fallback behavior in the platform aggregator.

### Changed
- Updated project version to `2.2.0`.
- Improved Deezer search error handling.
- Improved Deezer track loading error handling.
- Updated README for the v2.2.0 release.
- Updated roadmap and release workflow documentation.

### Fixed
- Fixed duplicated `admin_only` response in the `/errors` command.
- Ensured Spotify failures do not break track cards or Deezer-based results.

### Security
- Release package should not include `.env`, `.git`, `data/`, `logs/`, `.pytest_cache`, `.vscode` or `__pycache__` files.

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
- This release focuses on architecture and maintainability.
