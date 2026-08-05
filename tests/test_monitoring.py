import pytest
from fastapi.testclient import TestClient

import app.monitoring as monitoring
from tests.conftest import to_async


def test_health_returns_ok_status():
    client = TestClient(monitoring.create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_head_returns_ok_status():
    """
    Some uptime monitors (e.g. UptimeRobot's free tier) only send HEAD
    requests. HEAD must return 200 with no body, not 405.
    """
    client = TestClient(monitoring.create_app())

    response = client.head("/health")

    assert response.status_code == 200
    assert response.content == b""


def _fake_pool_ok():
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

    return fake_get_pool


def test_ready_head_returns_ok_when_database_is_reachable(monkeypatch):
    monkeypatch.setattr(monitoring, "get_pool", _fake_pool_ok())
    monkeypatch.setattr(monitoring, "_check_redis_ready", to_async(lambda: True))

    client = TestClient(monitoring.create_app())
    response = client.head("/ready")

    assert response.status_code == 200
    assert response.content == b""


def test_ready_returns_ok_when_database_is_reachable(monkeypatch):
    monkeypatch.setattr(monitoring, "get_pool", _fake_pool_ok())
    monkeypatch.setattr(monitoring, "_check_redis_ready", to_async(lambda: True))

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_unavailable_when_database_check_raises(monkeypatch):
    async def fake_get_pool():
        raise RuntimeError("pool not initialized")

    monkeypatch.setattr(monitoring, "get_pool", fake_get_pool)
    monkeypatch.setattr(monitoring, "_check_redis_ready", to_async(lambda: True))

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
    monkeypatch.setattr(monitoring, "_check_redis_ready", to_async(lambda: True))

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_ready_returns_unavailable_when_redis_check_fails(monkeypatch):
    monkeypatch.setattr(monitoring, "get_pool", _fake_pool_ok())
    monkeypatch.setattr(monitoring, "_check_redis_ready", to_async(lambda: False))

    client = TestClient(monitoring.create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_metrics_endpoint_returns_prometheus_text(monkeypatch):
    monkeypatch.setattr(monitoring, "_update_cert_expiry_metric", lambda: None)

    client = TestClient(monitoring.create_app())
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "bot_rate_limit_blocked_total" in response.text


@pytest.mark.asyncio
async def test_check_redis_ready_returns_true_when_no_redis_url(monkeypatch):
    monkeypatch.setattr(monitoring.settings, "REDIS_URL", None)
    assert await monitoring._check_redis_ready() is True


@pytest.mark.asyncio
async def test_check_redis_ready_returns_false_when_client_is_none(monkeypatch):
    import app.services.redis_client as redis_client_module

    monkeypatch.setattr(monitoring.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", None)
    assert await monitoring._check_redis_ready() is False


@pytest.mark.asyncio
async def test_check_redis_ready_returns_true_when_ping_succeeds(monkeypatch):
    import app.services.redis_client as redis_client_module

    class FakeRedis:
        async def ping(self):
            return True

    monkeypatch.setattr(monitoring.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", FakeRedis())
    assert await monitoring._check_redis_ready() is True


@pytest.mark.asyncio
async def test_check_redis_ready_returns_false_when_ping_raises(monkeypatch):
    import app.services.redis_client as redis_client_module

    class BrokenRedis:
        async def ping(self):
            raise ConnectionError("Redis down")

    monkeypatch.setattr(monitoring.settings, "REDIS_URL", "redis://localhost:6379")
    monkeypatch.setattr(redis_client_module, "_client", BrokenRedis())
    assert await monitoring._check_redis_ready() is False


def test_update_cert_expiry_metric_no_op_when_no_cert_path(monkeypatch):
    monkeypatch.setattr(monitoring.settings, "WEBHOOK_CERT_PATH", None)

    monitoring._update_cert_expiry_metric()  # must not raise


def test_update_cert_expiry_metric_sets_negative_on_bad_path(monkeypatch):
    monkeypatch.setattr(monitoring.settings, "WEBHOOK_CERT_PATH", "/nonexistent/cert.pem")

    monitoring._update_cert_expiry_metric()

    from prometheus_client import REGISTRY

    value = REGISTRY.get_sample_value("bot_tls_cert_expiry_days")
    assert value == -1.0


def test_update_cert_expiry_metric_parses_valid_cert(monkeypatch, tmp_path):
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=30))
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "test.pem"
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    monkeypatch.setattr(monitoring.settings, "WEBHOOK_CERT_PATH", str(cert_path))

    monitoring._update_cert_expiry_metric()

    from prometheus_client import REGISTRY

    value = REGISTRY.get_sample_value("bot_tls_cert_expiry_days")
    assert value is not None
    assert 28.0 < value < 31.0
