"""
Exercises the downgrade half of every Alembic revision against real PostgreSQL.

`upgrade()` runs on every deploy and in every CI job, so a mistake there is
found immediately. `downgrade()` has never been executed by anything: the
schema is raw SQL through `op.execute()`, so each one is hand-written, and the
only time they would run is a rollback — the worst moment to discover one is
wrong.

The revision that makes this worth the cost is b7d92e4f1a03. Four of the five
downgrades are plain DROPs, hard to get wrong. That one *recreates* the two
indexes its upgrade dropped as duplicates of a UNIQUE constraint, and must
recreate them exactly as the baseline declared them. A wrong column list or
name would not raise — it would leave the schema quietly different from what
the next revision expects.

What this does not endorse: three of the five downgrades drop tables holding
live user data, so `alembic downgrade` is not the production rollback path.
That is the pinned `sha-` image tag. This checks the mechanism is sound, not
that it should be used.

Runs against its own database, created and dropped here, because `downgrade
base` would otherwise destroy the schema the session-scoped `pg_schema`
fixture builds for every other test.
"""

import asyncio
import os
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

from tests.conftest import PROJECT_ROOT

ROUNDTRIP_DB = "migration_roundtrip_test"

SNAPSHOT_QUERIES = {
    "columns": """
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, column_name
    """,
    "constraints": """
        SELECT tc.table_name, tc.constraint_type, kcu.column_name
        FROM information_schema.table_constraints tc
        LEFT JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_type, kcu.column_name
    """,
    # indexdef is the full CREATE INDEX statement, so a changed column list or
    # sort order shows up as a different string.
    "indexes": """
        SELECT tablename, indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY tablename, indexdef
    """,
}


def run(coro):
    """Each call gets its own loop; alembic's env.py also uses asyncio.run()."""
    return asyncio.run(coro)


async def _fetch(dsn: str, query: str) -> list[tuple]:
    connection = await asyncpg.connect(dsn)
    try:
        return [tuple(record) for record in await connection.fetch(query)]
    finally:
        await connection.close()


async def _execute_on(dsn: str, statement: str) -> None:
    connection = await asyncpg.connect(dsn)
    try:
        await connection.execute(statement)
    finally:
        await connection.close()


def snapshot(dsn: str) -> dict[str, list[tuple]]:
    return {name: run(_fetch(dsn, query)) for name, query in SNAPSHOT_QUERIES.items()}


def with_database(dsn: str, database: str) -> str:
    parts = urlsplit(dsn)
    return urlunsplit(parts._replace(path=f"/{database}"))


def alembic_config() -> Config:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    return config


def alembic(dsn: str, action: str, revision: str) -> None:
    os.environ["ALEMBIC_DATABASE_URL"] = dsn
    try:
        getattr(command, action)(alembic_config(), revision)
    finally:
        os.environ.pop("ALEMBIC_DATABASE_URL", None)


@pytest.fixture
def roundtrip_dsn(pg_dsn):
    """A dedicated empty database, dropped afterwards whatever the test did."""
    admin_dsn = pg_dsn
    target = with_database(pg_dsn, ROUNDTRIP_DB)

    run(_execute_on(admin_dsn, f'DROP DATABASE IF EXISTS "{ROUNDTRIP_DB}"'))
    run(_execute_on(admin_dsn, f'CREATE DATABASE "{ROUNDTRIP_DB}"'))
    try:
        yield target
    finally:
        run(_execute_on(admin_dsn, f'DROP DATABASE IF EXISTS "{ROUNDTRIP_DB}" WITH (FORCE)'))


def test_downgrade_to_base_removes_every_table(roundtrip_dsn):
    alembic(roundtrip_dsn, "upgrade", "head")
    assert snapshot(roundtrip_dsn)["columns"], "nothing was created to begin with"

    alembic(roundtrip_dsn, "downgrade", "base")

    remaining = {
        table for table, *_ in snapshot(roundtrip_dsn)["columns"]
    } - {"alembic_version"}
    assert remaining == set(), f"downgrade left tables behind: {sorted(remaining)}"


def test_schema_is_identical_after_a_full_round_trip(roundtrip_dsn):
    """
    upgrade -> downgrade -> upgrade must land on the same schema.

    This is what catches b7d92e4f1a03 recreating an index under a different
    name or column list: the second upgrade would then build on a different
    starting point, and indexdef would differ.
    """
    alembic(roundtrip_dsn, "upgrade", "head")
    before = snapshot(roundtrip_dsn)

    alembic(roundtrip_dsn, "downgrade", "base")
    alembic(roundtrip_dsn, "upgrade", "head")
    after = snapshot(roundtrip_dsn)

    for name in SNAPSHOT_QUERIES:
        assert after[name] == before[name], (
            f"{name} differ after the round trip\n"
            f"  only before: {sorted(set(before[name]) - set(after[name]))}\n"
            f"  only after:  {sorted(set(after[name]) - set(before[name]))}"
        )


@pytest.mark.parametrize(
    "revision",
    ["bf5069cbb1be", "63ab83bf2873", "cf55a191898c", "a3f81c2d47e9", "b7d92e4f1a03"],
)
def test_every_revision_steps_down_and_back_up_cleanly(roundtrip_dsn, revision):
    """
    One revision at a time, so a failure names the offending migration instead
    of only saying the chain is broken somewhere.
    """
    alembic(roundtrip_dsn, "upgrade", revision)
    at_revision = snapshot(roundtrip_dsn)

    alembic(roundtrip_dsn, "downgrade", "base")
    alembic(roundtrip_dsn, "upgrade", revision)

    assert snapshot(roundtrip_dsn) == at_revision, f"{revision} is not idempotent"


def test_the_index_recreating_downgrade_restores_the_baseline_set(roundtrip_dsn):
    """
    b7d92e4f1a03 drops idx_users_telegram_id and idx_tracks_deezer_track_id as
    duplicates of UNIQUE constraints, and adds idx_tracks_artist_rank. Stepping
    back to the previous revision must restore exactly the earlier index set --
    the one case here where downgrade creates rather than drops.
    """
    alembic(roundtrip_dsn, "upgrade", "a3f81c2d47e9")
    before = {indexdef for _table, indexdef in snapshot(roundtrip_dsn)["indexes"]}

    alembic(roundtrip_dsn, "upgrade", "b7d92e4f1a03")
    at_head = {indexdef for _table, indexdef in snapshot(roundtrip_dsn)["indexes"]}

    # Sanity: the upgrade really did change the index set, so the comparison
    # below is not trivially true.
    assert at_head != before
    assert any("artist" in definition for definition in at_head)

    alembic(roundtrip_dsn, "downgrade", "a3f81c2d47e9")
    after = {indexdef for _table, indexdef in snapshot(roundtrip_dsn)["indexes"]}

    assert after == before, (
        "the recreated indexes do not match the baseline definitions\n"
        f"  lost:  {sorted(before - after)}\n"
        f"  extra: {sorted(after - before)}"
    )
