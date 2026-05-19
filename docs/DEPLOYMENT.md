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
python -m pip install -r requirements.txt
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

Run the bot:

```bash
python run.py
```

## Docker Run

Build the image:

```bash
docker build -t telegram-music-finder-bot .
```

Run the container:

```bash
docker run --env-file .env -v "%cd%/data:/app/data" -v "%cd%/logs:/app/logs" telegram-music-finder-bot
```

On Linux/macOS:

```bash
docker run --env-file .env -v "$(pwd)/data:/app/data" -v "$(pwd)/logs:/app/logs" telegram-music-finder-bot
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

## Data and Logs

The compose configuration mounts local folders:

```text
data/ -> /app/data
logs/ -> /app/logs
```

This keeps the SQLite database and log files outside the container image.

## GitHub Actions

The workflow runs:

```bash
python -m ruff check .
python -m pytest
docker build -t find-music-bot:test .
```

This checks code style, tests and Docker image build on every push or pull request.

## Security Notes

Never commit or publish:

```text
.env
data/
logs/
*.db
*.log
```

If `.env` was ever uploaded to GitHub or shared in an archive, regenerate Telegram, Genius and Spotify credentials.
