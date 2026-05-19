# v2.3.0 - Docker & Deployment Update

## Overview

This release focuses on deployment readiness. The project now includes Docker support, Docker Compose startup, deployment documentation and Docker build validation in GitHub Actions.

No new music platforms were added, and the main bot behavior remains unchanged.

## Added

- `Dockerfile` for containerized bot execution.
- `docker-compose.yml` for one-command local Docker startup.
- `.dockerignore` to exclude local/private files from Docker builds.
- `docs/DEPLOYMENT.md` with local, Docker and Docker Compose instructions.
- Docker build validation step in GitHub Actions.
- GitHub Actions status badge in README.

## Changed

- Updated project version to `2.3.0`.
- Updated README with Docker usage instructions.
- Updated `.env.example` with clearer environment variable descriptions.
- Updated roadmap and release workflow documentation.
- Updated architecture documentation with deployment layer details.

## Quality Checks

Before publishing this release, run:

```bash
python -m ruff check .
python -m pytest
docker build -t find-music-bot:test .
```

GitHub Actions also runs:

```text
Ruff
Pytest
Docker build
```

## Security / Cleanup

Do not commit or publish:

```text
.env
.git/
data/
logs/
.pytest_cache/
.vscode/
__pycache__/
*.pyc
*.db
*.log
```

If `.env` was ever uploaded to GitHub or shared in an archive, regenerate Telegram, Genius and Spotify credentials.
