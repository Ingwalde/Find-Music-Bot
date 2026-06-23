from fastapi.testclient import TestClient

import app.monitoring as monitoring


def test_health_returns_ok_status():
    client = TestClient(monitoring.create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ok_when_database_is_reachable(monkeypatch):
    class FakeConnection:
        async def fetchval(self, *args, **kwargs):
            return 1

    class FakeAcquireContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, *args):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquireContext()

    async def fake_get_pool():
        return FakePool()

    monkeypatch.setattr(monitoring, "get_pool", fake_get_pool)

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_unavailable_when_database_check_raises(monkeypatch):
    async def fake_get_pool():
        raise RuntimeError("pool not initialized")

    monkeypatch.setattr(monitoring, "get_pool", fake_get_pool)

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_ready_returns_unavailable_when_fetchval_raises(monkeypatch):
    class FakeConnection:
        async def fetchval(self, *args, **kwargs):
            raise RuntimeError("connection lost")

    class FakeAcquireContext:
        async def __aenter__(self):
            return FakeConnection()

        async def __aexit__(self, *args):
            return False

    class FakePool:
        def acquire(self):
            return FakeAcquireContext()

    async def fake_get_pool():
        return FakePool()

    monkeypatch.setattr(monitoring, "get_pool", fake_get_pool)

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
