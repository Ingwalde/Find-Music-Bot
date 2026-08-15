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
docker compose up -d --wait test-postgres test-redis
DATABASE_URL=postgresql://testuser:testpass@localhost:5433/testdb \
  REDIS_URL=redis://localhost:6380 \
  python -m pytest
docker compose stop test-postgres test-redis
```

**Windows PowerShell:**

```powershell
docker compose up -d --wait test-postgres test-redis
$env:DATABASE_URL = "postgresql://testuser:testpass@localhost:5433/testdb"
$env:REDIS_URL = "redis://localhost:6380"
python -m pytest
docker compose stop test-postgres test-redis
```

Both test services have healthchecks, so `--wait` blocks until they actually
accept connections instead of letting pytest race a still-starting container.

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

## Webhook Mode

Polling (`BOT_MODE=polling`, the default) needs no extra setup — skip this
section unless you specifically want webhook mode (added in v3.3.0).

Webhook mode (`BOT_MODE=webhook`) terminates TLS itself with a self-signed
certificate — there is no reverse proxy in front of it. Required `.env` values:

```env
BOT_MODE=webhook
WEBHOOK_PUBLIC_URL=https://your_public_ip_or_domain:8443
WEBHOOK_SECRET_PATH=your_random_secret_path
WEBHOOK_SECRET_TOKEN=your_random_secret_token
WEBHOOK_CERT_PATH=/app/certs/cert.pem
WEBHOOK_KEY_PATH=/app/certs/key.pem
WEBHOOK_PORT=8443
```

`WEBHOOK_SECRET_PATH` and `WEBHOOK_SECRET_TOKEN` should each be a long random
string you generate yourself — they are not values Telegram gives you.

### Generate the self-signed certificate

Run on the server, with `CN` set to its public IP address:

```bash
mkdir -p certs
openssl req -newkey rsa:2048 -sha256 -nodes -keyout certs/key.pem -x509 -days 365 \
  -out certs/cert.pem -subj "/CN=your_public_ip"
```

`docker-compose.yml` mounts `./certs` read-only into the container at
`/app/certs`, matching `WEBHOOK_CERT_PATH`/`WEBHOOK_KEY_PATH` above. Keep
`certs/key.pem` private — never commit it (see Security Notes below).

Telegram needs the public certificate registered once, via `set_webhook`'s
`certificate` parameter — the bot does this itself at startup in webhook mode
using `WEBHOOK_CERT_PATH`. No separate manual upload step is required.

### Certificate renewal

The certificate is valid 365 days from generation. Regenerate it yearly with
the same command above and restart the bot — set your own reminder, expiry is
not currently monitored automatically.

### Monitoring webhook health

Call `getWebhookInfo` on the Bot API to check the webhook's live state:

```bash
curl "https://api.telegram.org/bot<your_bot_token>/getWebhookInfo"
```

Watch `last_error_message` (set when Telegram's last delivery attempt failed)
and `pending_update_count` (updates queued because delivery is failing) —
either one being non-empty/non-zero means Telegram currently cannot reach the
webhook.

### Firewall

`docker-compose.yml` publishes both ports without a host-IP restriction —
restrict them at the network/cloud-firewall layer instead (e.g. Oracle Cloud's
Security List):

- **8443** (webhook) — open only to Telegram's webhook IP ranges:
  `149.154.160.0/20` and `91.108.4.0/22`. No other source needs access.
- **9090** (health/readiness) — open only to your own monitoring source's IP,
  never to `0.0.0.0`/the whole internet.

## Data, Logs and Config

The compose configuration mounts local folders:

```text
data/   -> /app/data
logs/   -> /app/logs
config/ -> /app/config:ro
certs/  -> /app/certs:ro
```

This keeps logs and local admin configuration outside the container image. `data/` is mounted
read-only for the historical SQLite backup file used only by the one-time
`scripts/migrate_sqlite_to_postgres.py` script — the live database is PostgreSQL, managed by its
own named volume (`postgres-data`), not this mount.

## GitHub Actions

### Tests workflow (`.github/workflows/tests.yml`)

Runs on every push and pull request:

1. **Ruff** — lint check
2. **mypy** — `python -m mypy` (checked module set lives in `pyproject.toml`)
3. **pip-audit** — known vulnerabilities in `requirements/base.txt`
4. **`alembic upgrade head`** — applies the schema against the CI Postgres service
5. **pytest with coverage** — full suite including the `test_*_pg.py` integration tests
6. **Release cleanup check** — `scripts/check_release_clean.py`
7. **Version consistency check** — `scripts/check_version_sync.py`
8. **Locale coverage check** — `scripts/check_locale_coverage.py`
9. **Docker build + push** — builds the image; on `main` pushes to `ghcr.io/ingwalde/find-music-bot:latest`
10. **Trivy image scan** — fails on fixable HIGH/CRITICAL findings in the built image

CI provisions a `postgres:16-alpine` service container
(`testuser`/`testpass`/`testdb`, port 5432) and injects
`DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb` so the
integration tests run against it — the same credentials as the local
`test-postgres` service, only the port differs (5432 on CI, 5433 locally).

### Deploy workflow (`.github/workflows/deploy.yml`)

Triggers automatically after the Tests workflow completes successfully on `main`
(`workflow_run` event — guarantees the GHCR image is pushed before deploy runs):

1. Copies `docker-compose.yml` to the server via SCP.
2. SSHs in and runs `docker logout ghcr.io` — the package is public, and a stale
   credential would make the daemon send an expired token instead of pulling
   anonymously.
3. `docker compose pull`. **A failed pull aborts the deploy.** It must: compose
   otherwise falls back to the locally cached image and the old container starts,
   and `/ready` then answers from stale code, turning a failed deploy green. That
   is exactly what happened after v3.7.7 — three deploys shipped nothing while
   reporting success.
4. Restarts the stack with `docker compose up -d --remove-orphans`, then asserts
   the running container's image ID equals the one just pulled.
5. Polls `http://localhost:9090/ready` every 3 s (up to 60 s). Fails the job and
   dumps 50 lines of `music-bot` logs if the bot does not become ready in time.

The whole script runs under `set -euo pipefail`, so any unhandled command failure
fails the deploy rather than being stepped over.

The server pulls the image anonymously from GHCR (the package is public — no
`docker login` required on the server).

### Dependency updates

Dependabot opens PRs against the long-lived `deps/staging` branch, not `main`
(`target-branch` in `.github/dependabot.yml`). `sync-deps-branch.yml` merges
`main` into `deps/staging` daily so those PRs never drift far enough behind to
conflict; on a merge conflict it opens an issue labelled `deps-sync` instead of
failing silently. Review and merge dependency PRs into `deps/staging`, then open
one PR from `deps/staging` to `main`.

## Security Notes

Never commit or publish:

```text
.env
config/admins.json
certs/
data/
logs/
*.db
*.log
coverage.xml
.coverage
```

If `.env` was ever uploaded to GitHub or shared in an archive, regenerate Telegram, Genius and Spotify credentials.
