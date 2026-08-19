import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config.settings import settings  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No SQLAlchemy ORM models in this project — migrations are raw SQL via
# op.execute(). target_metadata stays None; autogenerate is not used.
target_metadata = None


def _alembic_database_url() -> str:
    """
    Derives the SQLAlchemy async engine URL.

    Prefers ALEMBIC_DATABASE_URL when explicitly set. This exists for the
    live_pg test fixture, which needs to point Alembic at a testcontainers
    instance after the process has already started.

    v3.7.10 moved Settings to field(default_factory=...), so a *freshly
    constructed* Settings() now does read a late os.environ["DATABASE_URL"]
    (tests/test_stage1_quality.py pins that). This module does not construct
    one: it imports the module-level `settings` singleton, and that is built
    once when app.config.settings is imported. So a DATABASE_URL set later in
    the same pytest process still would not reach it, and the override is still
    load-bearing — for the singleton's lifetime, not for the reason the
    original comment gave.

    Making it a genuine convenience rather than a necessity means reading a
    fresh Settings() here instead of the singleton. That is a change to the
    migration path and belongs in its own release.

    Falls back to the app's DATABASE_URL setting otherwise — the normal
    CLI/deploy path (Stage 1/2 verification, production migrations).

    The app's asyncpg pool uses a bare postgresql:// DSN; SQLAlchemy's
    async engine needs the +asyncpg dialect suffix to select the asyncpg
    driver. The application runtime never sees any of this — it's only
    used here, to let Alembic connect using the right DSN for the context
    it's running in.
    """
    url = os.environ.get("ALEMBIC_DATABASE_URL") or settings.DATABASE_URL
    if url and url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


config.set_main_option("sqlalchemy.url", _alembic_database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
