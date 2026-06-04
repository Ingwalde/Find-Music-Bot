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

## Docker Run

Build the image:

```bash
docker build -f deploy/Dockerfile -t telegram-music-finder-bot .
```

Run the container on Windows PowerShell:

```bash
docker run --env-file .env -v "${PWD}/data:/app/data" -v "${PWD}/logs:/app/logs" -v "${PWD}/config:/app/config:ro" telegram-music-finder-bot
```

On Linux/macOS:

```bash
docker run --env-file .env -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/config:/app/config:ro" telegram-music-finder-bot
```

## Docker Compose Run

Start the bot:

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Run in the background:

```bash
docker compose -f deploy/docker-compose.yml up --build -d
```

Stop the bot:

```bash
docker compose -f deploy/docker-compose.yml down
```

View logs:

```bash
docker compose -f deploy/docker-compose.yml logs -f
```

## Data, Logs and Config

The compose configuration mounts local folders:

```text
data/   -> /app/data
logs/   -> /app/logs
config/ -> /app/config:ro
```

This keeps the SQLite database, logs and local admin configuration outside the container image.

## GitHub Actions

The workflow runs:

```bash
python -m ruff check .
python -m pytest --cov=app --cov-report=xml --cov-report=term-missing
docker build -f deploy/Dockerfile -t find-music-bot:test .
```

This checks code style, tests, coverage and Docker image build on every push or pull request.

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
