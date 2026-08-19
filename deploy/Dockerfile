# Build stage — pip and the wheels it downloads stay here and never reach
# the runtime image. Keeps the shipped image smaller and cuts the CVE surface
# Trivy has to scan (see the scan step in .github/workflows/tests.yml).
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements/base.txt requirements/base.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir --prefix=/install -r requirements/base.txt

# Runtime stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Apply Debian security updates on top of the base image. python:3.12-slim is
# rebuilt on its own schedule, so between rebuilds it ships OS packages with
# published fixes — CVE-2026-53615 in util-linux/libblkid1 blocked every build
# for exactly that reason. The Trivy gate runs with ignore-unfixed, meaning
# only CVEs the project *can* act on fail the build; upgrading here is that
# action. Without it the only options are pinning a base digest that ages the
# same way, or ignoring a fixable HIGH.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only the installed packages come across — no pip cache, no build wheels.
COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p data logs \
    && addgroup --system botuser \
    && adduser --system --ingroup botuser botuser \
    && chown -R botuser:botuser /app

USER botuser

# Cosmetic only — actual publishing is docker-compose.yml's job. Documents
# the webhook-mode (v3.3.0+) TLS port the app listens on when BOT_MODE=webhook.
EXPOSE 8443

# Schema setup is owned by Alembic (v3.1.1+) — run the migration chain
# before the bot starts. Idempotent: alembic upgrade head is a no-op if
# already at head, so this is safe on every container start/restart.
# `exec` replaces the shell with the Python process (same PID) so SIGTERM
# from `docker stop`/`compose down` reaches it directly instead of being
# swallowed by dash, letting the graceful-shutdown logic in app/main.py run.
CMD ["sh", "-c", "alembic upgrade head && exec python run.py"]
