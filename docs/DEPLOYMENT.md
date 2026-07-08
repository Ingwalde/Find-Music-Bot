# Deployment Guide

This guide explains how to run Telegram Music Finder Bot locally and with Docker.

## Requirements

- Python 3.12+
- Telegram bot token from BotFather
- Optional Genius token
- Optional Spotify Client ID and Client Secret
- Docker Desktop, if using Docker

## Local Run

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Activate it on Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements/base.txt
```

Create `.env`:

```bash
copy .env.example .env
```

On Linux/macOS:

```bash
cp .env.example .env
```

Fill in at least:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

## Admin Configuration

Admin-only features can be enabled through `ADMIN_ID` in `.env` or through a local admin config file.

Create the local admin config:

```bash
copy config\admins.example.json config\admins.json
```

On Linux/macOS:

```bash
cp config/admins.example.json config/admins.json
```

Example:

```json
{
  "admin_ids": [123456789]
}
```

Use your real Telegram user ID. The file `config/admins.json` is ignored by Git and should not be committed.

For Docker Compose, the whole local `config/` directory is mounted read-only:

```yaml
volumes:
  - ../data:/app/data
  - ../logs:/app/logs
  - ../config:/app/config:ro
```

This keeps `config/admins.json` outside the Docker image while still making it available to the running container.

## Run Bot Locally

```bash
python run.py
```

## Running Integration Tests

The nine `test_*_pg.py` files are PostgreSQL integration tests. They require
a running Postgres instance exposed via the `DATABASE_URL` environment variable.
Use the `test-postgres` Docker Compose service (port 5433, separate from the
bot's own Postgres on 5432):

**Bash / Linux / macOS:**

```bash
docker compose up -d test-postgres
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb python -m pytest
docker compose stop test-postgres
```

**Windows PowerShell:**

```powershell
docker compose up -d test-postgres
$env:DATABASE_URL = "postgresql://testuser:testpass@localhost:5433/testdb"
python -m pytest
docker compose stop test-postgres
```

To run only the non-PG tests (no database needed):

```bash
python -m pytest --ignore=tests/test_users_pg.py --ignore=tests/test_tracks_pg.py --ignore=tests/test_searches_pg.py --ignore=tests/test_favorites_pg.py --ignore=tests/test_errors_pg.py --ignore=tests/test_health_pg.py --ignore=tests/test_maintenance_pg.py --ignore=tests/test_search_cache_pg.py --ignore=tests/test_spotify_pg.py
```

The `test-postgres` service uses the `test` Docker Compose profile so it does
not start on plain `docker compose up`. Its data is ephemeral (no named volume)
and safe to discard between sessions.

## Docker Run

Build the image:

```bash
docker build -f deploy/Dockerfile -t tg-bot .
```

Run the container on Windows PowerShell:

```bash
docker run --env-file .env -v "${PWD}/data:/app/data" -v "${PWD}/logs:/app/logs" -v "${PWD}/config:/app/config:ro" tg-bot
```

On Linux/macOS:

```bash
docker run --env-file .env -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/config:/app/config:ro" tg-bot
```

## Docker Compose Run

Start the bot:

```bash
docker compose up --build
```

Run in the background:

```bash
docker compose up --build -d
```

Stop the bot:

```bash
docker compose down
```

View logs:

```bash
docker compose logs -f
```

## Data, Logs and Config

The compose configuration mounts local folders:

```text
data/   -> /app/data
logs/   -> /app/logs
config/ -> /app/config:ro
```

This keeps logs and local admin configuration outside the container image. `data/` is mounted
read-only for the historical SQLite backup file used only by the one-time
`scripts/migrate_sqlite_to_postgres.py` script — the live database is PostgreSQL, managed by its
own named volume (`postgres-data`), not this mount.

## GitHub Actions

The workflow (`.github/workflows/tests.yml`) runs on every push and pull request:

1. **Ruff** — lint check
2. **`alembic upgrade head`** — applies the schema against the CI Postgres service
3. **pytest with coverage** — full suite including the 9 `test_*_pg.py` integration tests
4. **Release cleanup check** — `scripts/check_release_clean.py`
5. **Locale coverage check** — `scripts/check_locale_coverage.py`
6. **Docker build** — `docker build -f deploy/Dockerfile -t find-music-bot:test .`

CI provisions a `postgres:16-alpine` service container
(`testuser`/`testpass`/`testdb`, port 5432) and injects
`DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb` so the
integration tests run against it — the same credentials as the local
`test-postgres` service, only the port differs (5432 on CI, 5433 locally).

## Security Notes

Never commit or publish:

```text
.env
config/admins.json
data/
logs/
*.db
*.log
coverage.xml
.coverage
```

If `.env` was ever uploaded to GitHub or shared in an archive, regenerate Telegram, Genius and Spotify credentials.
