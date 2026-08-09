# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)

Telegram Music Finder Bot is a Python Telegram bot for searching music, showing track information, saving favorites, viewing search history, opening lyrics pages, and providing admin maintenance tools.

---

## Why this project matters

Most Telegram bots are 100–300 line scripts. This one is a production-grade backend service
that happens to have a Telegram interface:

- **Layered architecture** — handlers, services, platforms, and repositories are separate layers with enforced import direction. No logic in handlers, no DB calls in services.
- **Production patterns** — Prometheus metrics, `/health` / `/ready` endpoints, graceful SIGTERM drain, circuit breaker, correlation IDs, Redis fallback — the same patterns used in real services.
- **Resilience** — every external call (Deezer, Spotify, Genius, Redis) has a fallback. The bot never crashes on a single service outage.
- **Schema discipline** — Alembic owns the database schema; the runtime uses raw asyncpg (no ORM). Every schema change is a versioned migration.
- **94%+ test coverage** — meaningful tests: concurrency scenarios, fallback paths, Redis integration, Prometheus counter increments, TLS cert parsing.

---

## Main Features

### Music Search

- Search tracks by title, artist, or free-text query.
- Uses Deezer as the main music data source.
- Shows paginated search results.
- Keeps temporary search context for pagination and track selection.
- Automatically cleans expired in-memory search contexts.

### Track Cards

Each selected track can show:

- Track title.
- Artist name.
- Album title.
- Duration.
- Release date when available.
- Popularity/rank label when available.
- Deezer track link.
- Cover image when available.
- Spotify link when available.
- Genius lyrics link when available.

After the track card, the bot automatically sends a "You may also like" block with related tracks by the same artist from the local database. If the database has no data for the artist, the bot fetches the artist's top tracks from Deezer as a fallback.

The track card also includes a 🎯 Similar inline button for quick access to tracks similar to the selected one using the Deezer radio endpoint.

### Smart Recommendations

- `/similar` — shows tracks similar to the last viewed track using the Deezer radio endpoint.
- `/trending` — shows the top tracks of the week from the Deezer chart. Results are cached
  for 1 hour to reduce API load. Cache is stored in Redis when available, in-memory otherwise.
- The last viewed track ID is saved in the database so `/similar` works across bot restarts.

### Platform Links

- Deezer is the primary search source.
- Spotify enrichment is optional and controlled by environment variables.
- Spotify failures do not break the main Deezer-based result flow.
- Spotify 403 responses trigger a temporary cooldown to avoid repeated failed lookups.
- Genius lyrics lookup is optional and disabled safely when `GENIUS_TOKEN` is not configured.

### Favorites

- Add tracks to favorites.
- Remove tracks from favorites.
- View saved favorites.
- Clear favorites with confirmation.
- Favorite state is stored in PostgreSQL.

### Search History

- Save user search queries.
- View recent search history.
- Re-run searches from history.
- Clear search history with confirmation.
- Search history is stored in PostgreSQL and can be trimmed by maintenance tools.

### Rate Limiting

- Per-user sliding-window rate limiting configurable via `RATE_LIMIT_MAX_REQUESTS` and
  `RATE_LIMIT_WINDOW_SECONDS`.
- Backed by Redis sorted set when `REDIS_URL` is set; falls back to in-memory.
- Admin users are unconditionally exempt.

### Localization

- Main menu and bot actions support multiple languages.
- Supported language set includes English, Ukrainian, Norwegian, German, French, Spanish, Italian, and Polish.
- English is the baseline language.
- Missing translation keys fall back to English.
- Locale coverage can be checked with a helper script.

### Admin Menu

Admin users can get an extra admin button in the main menu.

Admin access can be configured through:

- `ADMIN_ID` in `.env`.
- local `config/admins.json` based on `config/admins.example.json`.

The local `config/admins.json` file is ignored by Git and should not be committed.

Admin menu actions include:

- Statistics report.
- Maintenance report.
- Health report.
- Cleanup saved errors.
- Cleanup search history.
- Reload admin configuration cache.

Slash commands are also kept as fallback admin access:

```text
/errors           Show recent saved errors
/clear_errors     Clear saved errors
/health           Show runtime health checks
/stats            Show users/searches/favorites/tracks/errors statistics
/maintenance      Show database size, schema version and maintenance status
/cleanup_errors   Keep newest saved errors and remove older rows
/cleanup_history  Keep newest search history rows per user and remove older rows
```

### Admin Diagnostics

Admin diagnostics include:

- Bot version.
- Database status.
- Redis status.
- Database path.
- Database size.
- Table counts.
- Schema version.
- Spotify availability/cooldown status.
- Genius configuration status.
- Recent saved errors.

### Monitoring Endpoints

FastAPI runs alongside the bot on port 9090:

- `GET /health` — liveness: bot, database, Redis, Spotify, Deezer, Genius.
- `GET /ready` — readiness: database and Redis (503 if either is configured but unreachable).
- `GET /metrics` — Prometheus metrics: API request counts and latency, circuit breaker
  state, cache hit/miss counters, rate-limit blocked counter, TLS cert expiry gauge.

### Database and Persistence

The project uses PostgreSQL for persistence, accessed via asyncpg with a connection pool.

Stored data includes:

- Users.
- Tracks.
- Favorites.
- Search history.
- Spotify cached links.
- Error history.
- Admin audit log.
- Alembic schema version (`alembic_version` table).

Database features:

- Async connection pool (asyncpg).
- Schema and indexes owned by Alembic migrations (`migrations/versions/`),
  applied with `alembic upgrade head` at container start.
- Repository modules split by domain.
- Compatibility repository facade for stable imports.
- Database maintenance helpers.
- One-time SQLite→PostgreSQL migration script.

### Error Logging

- Runtime errors can be saved into the database.
- Error logging is designed not to crash the bot if the database is unavailable.
- Admins can inspect and clear saved errors.

### Testing and Quality

The project includes automated quality checks:

- Pytest test suite (~94% coverage, minimum gate 85%).
- Coverage reporting through `pytest-cov`.
- Ruff linting.
- mypy on typed modules.
- GitHub Actions workflow.
- Release cleanup validation script.
- Locale coverage checker.
- Env variable documentation checker.

Useful commands:

```bash
python -m ruff check .
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
python scripts/check_env_example.py
```

### Docker Support

The Dockerfile lives in `deploy/`; `docker-compose.yml` is in the project root
(so `docker compose` auto-loads `.env` — no `-f`/`--env-file` flags needed).

The Compose stack includes:

- `music-bot` — the bot process.
- `postgres` — PostgreSQL database with health check and named volume.
- `redis` — Redis 7 (alpine) for rate limiting and trending cache. `music-bot` waits for
  it with `condition: service_healthy`.
- `test-postgres` and `test-redis` — ephemeral services under the `test` profile for
  local integration tests.

Build image:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

Run with Docker Compose:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

Docker Compose mounts:

- `data/` — read-only access to the historical SQLite backup file, used only by the one-time
  `scripts/migrate_sqlite_to_postgres.py` migration script. The live database is PostgreSQL,
  managed by its own named volume (`postgres-data`), not this mount.
- `logs/` to persist logs.
- `config/` as read-only config for admin IDs.

---

## Tech Stack

- Python 3.12
- aiogram 3.x
- httpx (Deezer search, Genius lyrics)
- Spotify Web API
- PostgreSQL (asyncpg)
- Alembic
- Redis (redis-py asyncio)
- FastAPI
- prometheus-client
- cryptography
- pytest / pytest-cov / pytest-asyncio / hypothesis
- Ruff
- mypy
- GitHub Actions
- Docker / Docker Compose

---

## Project Structure

```text
app/
├── bot/                 # Telegram handlers, callbacks, keyboards and user flows
├── config/              # Environment settings and admin access config
├── database/            # PostgreSQL repositories and maintenance helpers (schema owned by Alembic — see migrations/)
├── localization/        # Translations, languages and fallback translator
├── platforms/           # Platform integrations, Spotify modules and aggregator
├── services/            # Deezer, lyrics, formatting, Redis client and platform service facades
├── utils/               # Logging, text and time helpers
├── admin_tools.py       # Admin statistics, maintenance and cleanup reports
├── health.py            # Admin health diagnostics (bot, DB, Redis, platforms)
├── main.py              # Bot startup and lifecycle
├── monitoring.py        # FastAPI /health, /ready, /metrics endpoints
└── version.py           # Project version

config/
└── admins.example.json  # Public admin config template

deploy/
└── Dockerfile           # Container image definition

docker-compose.yml       # Compose stack (bot, postgres, redis, test services) — project root

docs/                    # Architecture, deployment, roadmap and release workflow docs
migrations/              # Alembic schema migrations (versions/, env.py) — schema source of truth
requirements/
├── base.txt             # Production dependencies
└── dev.txt              # Development and test dependencies
scripts/                 # Release, cleanup and quality helper scripts
tests/                   # Automated tests
.github/workflows/       # GitHub Actions CI
```

---

## Setup

### 1. Clone repository

```bash
git clone https://github.com/Ingwalde/Find-Music-Bot.git
cd Find-Music-Bot
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

Production dependencies:

```bash
python -m pip install -r requirements/base.txt
```

Development dependencies:

```bash
python -m pip install -r requirements/dev.txt
```

### 4. Create `.env`

Copy `.env.example` to `.env` and fill in your tokens.

Windows:

```bash
copy .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Required:

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql://music_user:changeme@postgres:5432/music_bot
```

The bot refuses to start if `DATABASE_URL` is missing. When using Docker
Compose, `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` must match the
credentials in `DATABASE_URL` — see `.env.example`.

Optional:

```env
GENIUS_TOKEN=your_genius_token_here
SPOTIFY_ENABLED=true
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_MARKET=NO
ADMIN_ID=your_telegram_user_id
LOG_FILE_PATH=logs/bot.log
LOG_LEVEL=INFO
BOT_MODE=polling
REDIS_URL=redis://redis:6379
RATE_LIMIT_MAX_REQUESTS=20
RATE_LIMIT_WINDOW_SECONDS=60
SHUTDOWN_TIMEOUT_SECONDS=30
```

> `DATABASE_PATH` also appears in `.env.example`, but it is only read by the
> one-time `scripts/migrate_sqlite_to_postgres.py` migration script — the live
> database is PostgreSQL and needs `DATABASE_URL`.

> `REDIS_URL` is optional. When omitted, rate limiting and trending cache fall back
> to in-memory implementations.

### 5. Configure local admin IDs

Copy the example file:

```bash
copy config\admins.example.json config\admins.json
```

Linux/macOS:

```bash
cp config/admins.example.json config/admins.json
```

Example:

```json
{
  "admin_ids": [123456789]
}
```

`config/admins.json` is local-only and should not be committed.

---

## Running Locally

```bash
python run.py
```

Expected log:

```text
Bot started successfully.
```

---

## Running with Docker

Build image:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

Start with Compose:

```bash
docker compose up --build
```

Start in background:

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

### Webhook Mode (optional)

Polling is the default and needs no extra setup. To run in webhook mode instead
(`BOT_MODE=webhook`), including self-signed certificate generation and required
firewall rules, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#webhook-mode).

---

## Development Checks

Run before committing:

```bash
python -m ruff check .
python -m mypy app/utils/types.py app/services/deezer_service.py app/platforms/aggregator.py app/services/track_formatter.py app/services/recommendations_service.py
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
python scripts/check_env_example.py
```

`python -m pytest` runs the full suite including PostgreSQL and Redis integration tests
and requires `DATABASE_URL` to be set. Start the test services first:

Bash:

```bash
docker compose up -d test-postgres test-redis
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb REDIS_URL=redis://localhost:6380 python -m pytest
```

PowerShell:

```powershell
docker compose up -d test-postgres test-redis
$env:DATABASE_URL = "postgresql://testuser:testpass@localhost:5433/testdb"
$env:REDIS_URL = "redis://localhost:6380"
python -m pytest
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full integration test details.

Docker check:

```bash
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

---

## Release Safety

Do not commit or upload local/private files:

```text
.env
config/admins.json
certs/
.git/
data/
logs/
.pytest_cache/
.ruff_cache/
.vscode/
__pycache__/
coverage.xml
.coverage
*.pyc
*.zip
```

Use this check before release:

```bash
python scripts/check_release_clean.py
```

Avoid sharing raw `docker compose config` output because it can expose secrets from `.env`.

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for completed releases and planned next stages.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full version history.

---

## License

[Polyform Noncommercial License 1.0.0](LICENSE) — free for personal, educational, and
non-commercial use. Commercial use requires explicit permission from the author.
