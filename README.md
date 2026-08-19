# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-PolyForm%20NC-lightgrey)

Search music, open track cards, save favorites and get recommendations — from a Telegram chat.
Under the interface it is an async backend service: PostgreSQL with versioned migrations, Redis
caching with in-memory fallback, a circuit breaker on every third-party call, Prometheus metrics
and graceful shutdown.

```text
Telegram → aiogram handlers → services → Deezer / Spotify / Genius
                                   ↓
                        PostgreSQL (asyncpg) + Redis
```

---

## Screenshots

> **TODO:** add real screenshots to `screenshots/` and link them here.
> See [`screenshots/README.md`](screenshots/README.md) for the recommended shots
> (start menu, search results, track card, favorites, history) and the rules on
> scrubbing tokens and personal data first.

---

## Architecture

Full diagrams and layer responsibilities: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

```mermaid
flowchart LR
    TG["Telegram API"] --> BOT["aiogram 3 dispatcher<br/>handlers · callbacks · middlewares"]
    BOT --> SVC["Services<br/>Deezer · recommendations · cache"]
    SVC --> PLAT["Platforms<br/>Spotify · aggregator"]
    BOT --> REPO["Repositories<br/>(asyncpg)"]
    SVC --> REPO
    REPO --> PG[("PostgreSQL")]
    SVC --> RD[("Redis")]
    BOT -.-> MON["FastAPI :9090<br/>/health /ready /metrics"]
```

Every outbound call goes through a shared retry + circuit-breaker layer
(`app/utils/http_retry.py`) that honours `Retry-After`, retries only on 5xx/429/timeout,
and opens per-service with a single-probe half-open state.

---

## Engineering highlights

- **Two migrations carried out on a running project.** The bot moved from the synchronous
  pyTelegramBotAPI to async **aiogram 3**, and from SQLite to **PostgreSQL** — the trail is in
  [`docs/CODE_REVIEW_ACTION_PLAN.md`](docs/CODE_REVIEW_ACTION_PLAN.md) and
  [`CHANGELOG.md`](CHANGELOG.md).
- **Type checking that found real bugs.** mypy used to run on a hand-picked list of 25 modules.
  Extending it to the whole `app` package surfaced **91 genuine type errors** in the modules
  nobody was checking — including a `None` dereference that crashed every callback on a message
  older than 48 hours. The checked set is now the package itself, so a new module cannot be
  added without passing (`pyproject.toml`).
- **Degrades instead of failing.** Deezer, Spotify, Genius and Redis each have a fallback path.
  Redis down → in-memory rate limiting and cache. Spotify 403 → cooldown, Deezer results still
  ship. No single dependency can take the bot down.
- **Graceful shutdown that actually drains.** SIGTERM stops new updates, waits for in-flight
  handlers, then tears down bot session → DB pool → Redis → HTTP client in order
  (`app/main.py`, `app/bot/shutdown_middleware.py`). The Dockerfile uses `exec` so the signal
  reaches Python.
- **Alembic owns the schema.** 4 versioned migrations applied on container start; the runtime
  uses raw asyncpg with no ORM.
- **Tested against real infrastructure, not mocks.** Integration tests build the schema
  *through Alembic* on a real PostgreSQL and flush a real Redis, so the SQL is exercised rather
  than stubbed. Plus Hypothesis property tests and concurrency scenarios. Coverage gate: 85%.
- **Deploys are verified, not assumed.** After a silent stale-image deploy in v3.7.8, the deploy
  workflow now aborts on a failed `compose pull` and compares the running container's image
  digest against the pulled one before polling `/ready`.
- **Observability built in.** Prometheus metrics (API latency, circuit-breaker state, cache
  hit/miss, rate-limit blocks, TLS expiry), correlation IDs through every handler, four alert
  rules and a Grafana dashboard in `deploy/`.

### Honest scope note

The layering is a convention, not a compiler-enforced boundary: `app/bot` modules currently call
`app.database.repositories` directly for lightweight lookups such as the user's language, and two
services read from the cache tables. Tightening this — and adding an import-direction check to
`tests/test_architecture_imports.py` so it is enforced rather than intended — is tracked in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Tech stack

| Layer          | Stack                                                          |
| -------------- | -------------------------------------------------------------- |
| **Bot**        | Python 3.12 · aiogram 3.x                                       |
| **Data**       | PostgreSQL (asyncpg) · Alembic · Redis 7                        |
| **HTTP**       | httpx · custom retry + circuit breaker                          |
| **Sources**    | Deezer API · Spotify Web API · Genius                           |
| **Ops**        | FastAPI (`/health` `/ready` `/metrics`) · prometheus-client · Grafana |
| **Quality**    | pytest · pytest-cov · hypothesis · Ruff · mypy · pip-audit · Trivy |
| **Delivery**   | Docker · Docker Compose · GitHub Actions · GHCR                 |

---

## Features

<details>
<summary><b>Music search &amp; track cards</b></summary>

- Search by title, artist or free text; paginated results backed by Deezer.
- Search context stored in Redis (1 h TTL) so pagination survives a restart; in-memory otherwise.
- Track cards show title, artist, album, duration, release date, rank, cover art, and Deezer /
  Spotify / Genius links when available.
- Each card is followed by a "You may also like" block from the local database, falling back to
  the artist's Deezer top tracks.
</details>

<details>
<summary><b>Recommendations</b></summary>

- `/similar` — tracks similar to the last viewed one (Deezer radio endpoint); the last track ID is
  persisted so it survives restarts.
- `/trending` — weekly Deezer chart, cached 1 h in Redis with an in-memory fallback tier.
- 🎯 Similar inline button on every track card.
</details>

<details>
<summary><b>Favorites &amp; history</b></summary>

- Add, remove, list and clear favorites (with confirmation), stored in PostgreSQL.
- Search history with re-run from history, clear with confirmation, trimmable by maintenance tools.
</details>

<details>
<summary><b>Rate limiting &amp; localization</b></summary>

- Per-user sliding window (`RATE_LIMIT_MAX_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`), Redis sorted
  set with in-memory fallback. Admins exempt.
- 8 languages — English (baseline), Ukrainian, Norwegian, German, French, Spanish, Italian,
  Polish. Missing keys fall back to English; coverage checked by a script in CI.
</details>

<details>
<summary><b>Admin tools</b></summary>

Admins are configured via `ADMIN_ID` or a git-ignored `config/admins.json`. Menu and slash commands
cover statistics, maintenance, health diagnostics, error inspection and cleanup, plus admin cache
reload. Every admin action is written to an audit log.

```text
/errors  /clear_errors  /health  /stats  /maintenance  /cleanup_errors  /cleanup_history
```
</details>

<details>
<summary><b>Monitoring endpoints</b></summary>

FastAPI runs alongside the bot on port 9090:

- `GET /health` — liveness: bot, database, Redis, Spotify, Deezer, Genius.
- `GET /ready` — readiness: database and Redis (503 if configured but unreachable).
- `GET /metrics` — Prometheus metrics.
</details>

---

## Quick start

```bash
git clone https://github.com/Ingwalde/Find-Music-Bot.git
cd Find-Music-Bot
cp .env.example .env          # fill in BOT_TOKEN and DATABASE_URL
docker compose up --build
```

`docker-compose.yml` sits in the project root so `docker compose` auto-loads `.env`. The stack
brings up the bot, PostgreSQL and Redis; migrations run on container start.

<details>
<summary><b>Running without Docker</b></summary>

```bash
python -m venv venv
source venv/bin/activate                    # Windows: venv\Scripts\activate
python -m pip install -r requirements/base.txt
python run.py
```
</details>

### Required configuration

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql://music_user:changeme@postgres:5432/music_bot
```

The bot refuses to start without `DATABASE_URL`. Under Compose, `POSTGRES_USER` /
`POSTGRES_PASSWORD` / `POSTGRES_DB` must match it. Optional: `REDIS_URL`, `GENIUS_TOKEN`,
`SPOTIFY_*`, `ADMIN_ID`, `LOG_LEVEL`, `BOT_MODE`, rate-limit and shutdown timeouts — all
documented in [`.env.example`](.env.example), which CI checks stays in sync with the code.

Admin IDs: copy `config/admins.example.json` to `config/admins.json` (git-ignored).

Webhook mode and TLS setup: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md#webhook-mode).

---

## Development

```bash
python -m ruff check .
python -m mypy                                   # the whole app package
python -m pytest --cov=app --cov-report=term-missing
```

The suite includes PostgreSQL and Redis integration tests, so start the test services first:

```bash
docker compose up -d test-postgres test-redis
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb \
REDIS_URL=redis://localhost:6380 \
python -m pytest
```

Four consistency checks also run in CI — they fail the build if `.env.example`, the version
constant, locale coverage or release hygiene drift out of sync:

```bash
python scripts/check_env_example.py
python scripts/check_version_sync.py
python scripts/check_locale_coverage.py
python scripts/check_release_clean.py
```

CI additionally runs `pip-audit` and a Trivy image scan that fails on HIGH/CRITICAL.

---

## Project layout

```text
app/
├── bot/           # aiogram handlers, callbacks, keyboards, middlewares
├── services/      # Deezer, recommendations, cache, formatting, Redis client
├── platforms/     # Spotify client/auth/matcher, aggregator
├── database/      # asyncpg repositories (split by domain) + maintenance
├── localization/  # 8 locales with English fallback
├── utils/         # retry/circuit breaker, correlation IDs, logging, metrics
├── main.py        # startup, task supervision, ordered shutdown
└── monitoring.py  # FastAPI /health /ready /metrics

migrations/        # Alembic — schema source of truth
deploy/            # Dockerfile, Prometheus alerts, Grafana dashboard
docs/              # architecture, deployment, metrics, roadmap
tests/             # unit, integration (real Postgres/Redis) and property tests
```

Test code outweighs application code, roughly 1.2 : 1.

---

## Documentation

| Document | Contents |
| -------- | -------- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Layer diagram and responsibilities |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Deployment, webhook mode, integration tests |
| [`docs/metrics.md`](docs/metrics.md) | Exported Prometheus metrics |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Completed releases and planned work |
| [`CHANGELOG.md`](CHANGELOG.md) | Full version history |

---

## License

[PolyForm Noncommercial License 1.0.0](LICENSE) — free for personal, educational and
non-commercial use. Commercial use requires explicit permission. Source-available, not an
OSI open-source license.
