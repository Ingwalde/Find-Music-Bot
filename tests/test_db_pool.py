import pytest

import app.database.db as db_module


@pytest.fixture(autouse=True)
def reset_pool():
    """Ensures _pool is None before and after every test in this file."""
    db_module._pool = None
    yield
    db_module._pool = None


class FakeConn:
    """Discards all SQL — used in pool lifecycle tests where DDL content is irrelevant."""

    async def execute(self, sql, *args):
        pass

    async def fetch(self, sql, *args):
        return []


class FakePool:
    def __init__(self):
        self.closed = False
        self._conn = FakeConn()

    def acquire(self):
        return self  # self acts as the async context manager

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        pass

    async def close(self):
        self.closed = True


# ── get_pool ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pool_raises_before_init():
    with pytest.raises(RuntimeError, match="Pool not initialized"):
        await db_module.get_pool()


# ── init_db_pool ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_init_db_pool_creates_pool(monkeypatch):
    created = []

    async def fake_create_pool(dsn, **kwargs):
        created.append(dsn)
        return FakePool()

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(db_module.settings, "DATABASE_URL", "postgresql://test/db")

    await db_module.init_db_pool()

    assert len(created) == 1
    assert created[0] == "postgresql://test/db"
    assert db_module._pool is not None


@pytest.mark.asyncio
async def test_init_db_pool_is_idempotent(monkeypatch):
    created = []

    async def fake_create_pool(dsn, **kwargs):
        created.append(1)
        return FakePool()

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(db_module.settings, "DATABASE_URL", "postgresql://test/db")

    await db_module.init_db_pool()
    await db_module.init_db_pool()

    assert len(created) == 1


# ── get_pool after init ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pool_returns_pool_after_init(monkeypatch):
    fake_pool = FakePool()

    async def fake_create_pool(dsn, **kwargs):
        return fake_pool

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(db_module.settings, "DATABASE_URL", "postgresql://test/db")

    await db_module.init_db_pool()

    assert await db_module.get_pool() is fake_pool


# ── close_db_pool ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_db_pool_closes_and_resets(monkeypatch):
    fake_pool = FakePool()

    async def fake_create_pool(dsn, **kwargs):
        return fake_pool

    monkeypatch.setattr(db_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(db_module.settings, "DATABASE_URL", "postgresql://test/db")

    await db_module.init_db_pool()
    await db_module.close_db_pool()

    assert fake_pool.closed is True
    assert db_module._pool is None


@pytest.mark.asyncio
async def test_close_db_pool_safe_when_not_initialized():
    await db_module.close_db_pool()
    assert db_module._pool is None
