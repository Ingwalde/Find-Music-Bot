FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/base.txt requirements/base.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements/base.txt

COPY . .

RUN mkdir -p data logs \
    && addgroup --system botuser \
    && adduser --system --ingroup botuser botuser \
    && chown -R botuser:botuser /app

USER botuser

# Schema setup is owned by Alembic (v3.1.1+) — run the migration chain
# before the bot starts. Idempotent: alembic upgrade head is a no-op if
# already at head, so this is safe on every container start/restart.
# `exec` replaces the shell with the Python process (same PID) so SIGTERM
# from `docker stop`/`compose down` reaches it directly instead of being
# swallowed by dash, letting the graceful-shutdown logic in app/main.py run.
CMD ["sh", "-c", "alembic upgrade head && exec python run.py"]
