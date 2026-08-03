# Telegram Music Finder Bot

[![Tests](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml/badge.svg)](https://github.com/Ingwalde/Find-Music-Bot/actions/workflows/tests.yml)

**Current version:** `v3.3.3 — Documentation Fixes`

Telegram Music Finder Bot is a Python Telegram bot for searching music, showing track information, saving favorites, viewing search history, opening lyrics pages, and providing admin maintenance tools.

The project is built as a backend-style portfolio project with modular architecture, PostgreSQL persistence via asyncpg, external API integrations, localization, logging, automated tests, coverage reports, Ruff checks, GitHub Actions, Docker support, release cleanup checks, admin diagnostics, database maintenance tools, and versioned releases.

---

## What Changed in v3.3.3

- `DATABASE_URL` is now correctly documented as **required** in the Setup section — the
  bot refuses to start without it. Previously the README listed only `BOT_TOKEN`.
- Removed the stale `DATABASE_PATH` line from the optional env block (it is migration-only)
  and corrected the "Database features" and "Stored data" sections to reflect Alembic
  ownership of the schema (in place since v3.1.1).
- Fixed the Docker Support section and Project Structure to show `docker-compose.yml` in
  the project root (moved there in v3.2.0), not under `deploy/`.
- Documentation-only patch. No code behavior changes.

---

## What Changed in v3.3.2

- Added a circuit breaker for network-level outages against Spotify, Deezer, or Genius —
  after 3 consecutive fully-failed calls to one service, further requests to it are
  short-circuited for a cooldown period instead of repeatedly retrying a service that's
  unreachable.
- Added a global error handler so an unexpected failure now always gets logged and
  recorded, instead of silently dropping the interaction.
- The lyrics lookup now shows a "searching..." status message while it looks up the
  Genius page.
- Various internal reliability fixes (see [CHANGELOG.md](CHANGELOG.md) for details). No
  breaking changes.

---

## What Changed in v3.3.1

- Backfilled the missing v3.1.2 CHANGELOG entry.
- Removed a stale `testcontainers` line from Tech Stack and replaced the stale Roadmap
  block with a pointer to [docs/ROADMAP.md](docs/ROADMAP.md).
- Documentation-only patch. No code behavior changes.

---

## What Changed in v3.3.0

- Added optional Telegram webhook mode as an alternative to polling, selected with
  `BOT_MODE=webhook` in `.env`. Default stays `BOT_MODE=polling` — no config change
  means no behavior change.
- Webhook mode terminates TLS itself with a self-signed certificate (no reverse proxy)
  and listens on port 8443. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for setup,
  certificate generation, and required firewall rules.
- `docker-compose.yml` publishes port 8443 and mounts `./certs` read-only for the
  certificate and private key.
- No user-facing feature changes — polling remains the default transport.

---

## What Changed in v3.2.0

- Added HTTP monitoring endpoints via FastAPI, running alongside the bot's aiogram polling
  in the same process: `GET /health` (liveness) and `GET /ready` (PostgreSQL readiness),
  served on port 9090.
- `docker-compose.yml` moved from `deploy/` to the project root — `docker compose` commands
  no longer need `-f`/`--env-file` flags. The Dockerfile stays in `deploy/`.
- The Dockerfile now execs the bot as PID 1, so `docker stop`/`docker compose down` delivers
  SIGTERM directly and the bot shuts down gracefully instead of being hard-killed.
- No user-facing feature changes.

---

## What Changed in v3.1.1

- Replaced the hand-built schema-migration mechanism with Alembic (industry-standard tooling).
  Alembic now owns the database schema; the app runtime stays on asyncpg.
- Schema is applied via `alembic upgrade head` at container start.
- `init_db_pool()` now only creates the connection pool — schema setup moved to Alembic.
- Fixed a facade-rule violation in `aggregator.py`.
- No user-facing feature changes.

---

## What Changed in v3.1.0

- Migrated the database from SQLite to PostgreSQL (asyncpg). All database access is now fully asynchronous via a connection pool.
- `asyncio.to_thread` wrappers removed — all DB calls are natively async.
- `deploy/docker-compose.yml` now includes a PostgreSQL service with healthcheck and named volume.
- `scripts/migrate_sqlite_to_postgres.py` provided for one-time data migration from existing SQLite files.
- `DATABASE_URL` is now required at startup.
- No user-facing feature changes.

---

## What Changed in v3.0.0

- **Full migration from pyTelegramBotAPI to aiogram 3.29.0.** All handlers, callbacks, and bot lifecycle code are now async.
- Removed legacy dependencies: `pyTelegramBotAPI`, `deezer-python`, `lyricsgenius`, `requests`.
- Deezer search and lyrics fetching now use `httpx` directly (no third-party SDKs).
- All sync DB and I/O calls use `asyncio.to_thread` for non-blocking execution.
- Dispatcher now wires `handlers_router` and `callbacks_router` at startup and drops pending updates before polling.
- Database schema, localization, and all user-facing features unchanged.

---

## What Changed in v2.7.0

- Internal technical-debt refactor — no new user-facing features.
- `/similar` now displays results grouped as `🎤 Artist / 🎵 Others`, matching the inline 🎯 Similar button.
- `/trending` formatting is now shared with the recommendations service (output unchanged).
- Removed dead code, unused facade exports, and duplicated handler boilerplate.
- All database repository functions now close their connection safely even on errors.

---

## What Changed in v2.6.1

- Localized favorites error alerts, which were previously shown in English regardless of the user's language.
- Localized the `/version` command output.
- Added error handling to the language selection callback.
- Track card errors are now logged to the admin error log instead of only the application log file.
- Improved test coverage for favorites and history callbacks.

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
- `/trending` — shows the top tracks of the week from the Deezer chart. Results are cached in-memory for 1 hour to reduce API load.
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
- Database path.
- Database size.
- Table counts.
- Schema version.
- Spotify availability/cooldown status.
- Genius configuration status.
- Recent saved errors.

### Database and Persistence

The project uses PostgreSQL for persistence, accessed via asyncpg with a connection pool.

Stored data includes:

- Users.
- Tracks.
- Favorites.
- Search history.
- Spotify cached links.
- Error history.
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

- Pytest test suite.
- Coverage reporting through `pytest-cov`.
- Minimum coverage gate.
- Ruff linting.
- GitHub Actions workflow.
- Release cleanup validation script.
- Locale coverage checker.

Useful commands:

```bash
python -m ruff check .
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
```

### Docker Support

The Dockerfile lives in `deploy/`; `docker-compose.yml` is in the project root
(so `docker compose` auto-loads `.env` — no `-f`/`--env-file` flags needed).

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

- Python
- aiogram
- httpx (Deezer search, Genius lyrics)
- Spotify Web API
- PostgreSQL (asyncpg)
- Alembic
- pytest
- pytest-cov
- pytest-asyncio
- Ruff
- GitHub Actions
- Docker
- Docker Compose

---

## Project Structure

```text
app/
├── bot/                 # Telegram handlers, callbacks, keyboards and user flows
├── config/              # Environment settings and admin access config
├── database/            # PostgreSQL repositories and maintenance helpers (schema owned by Alembic — see migrations/)
├── localization/        # Translations, languages and fallback translator
├── platforms/           # Platform integrations, Spotify modules and aggregator
├── services/            # Deezer, lyrics, formatting and platform service facades
├── utils/               # Logging, text and time helpers
├── admin_tools.py       # Admin statistics, maintenance and cleanup reports
├── health.py            # Admin health diagnostics
├── main.py              # Bot startup
└── version.py           # Project version

config/
└── admins.example.json  # Public admin config template

deploy/
└── Dockerfile           # Container image definition

docker-compose.yml       # Compose stack (bot, postgres, test-postgres) — project root

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
```

> `DATABASE_PATH` also appears in `.env.example`, but it is only read by the
> one-time `scripts/migrate_sqlite_to_postgres.py` migration script — the live
> database is PostgreSQL and needs `DATABASE_URL`.

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
python -m pytest --cov=app --cov-report=term-missing
python scripts/check_release_clean.py
python scripts/check_locale_coverage.py
python -c "from app.version import __version__; print(__version__)"
```

`python -m pytest` runs the full suite including PostgreSQL integration tests
and requires `DATABASE_URL` to be set. Start the test database first:

Bash:

```bash
docker compose up -d test-postgres
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb python -m pytest
```

PowerShell:

```powershell
docker compose up -d test-postgres
$env:DATABASE_URL = "postgresql://testuser:testpass@localhost:5433/testdb"
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

## Notes

This project is intended as a portfolio backend/bot project. It focuses on practical Telegram bot functionality, API integration, local persistence, maintainability, testing, Docker deployment and production-style cleanup practices.
