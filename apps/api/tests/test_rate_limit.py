from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings
from app.core.rate_limit import default_rate_limiter
from app.db.base import Base
from app.db.session import get_session
from app.integrations.redis import get_redis
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_rate_limit_state():
    default_rate_limiter.reset_memory()
    yield
    default_rate_limiter.reset_memory()


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter_in_memory():
    # Test checking limit of 3 in a 60s window
    key = "test_key_1"
    limit = 3
    window = 60

    # First 3 should succeed
    for i in range(3):
        allowed, remaining, reset_epoch, retry_after = await default_rate_limiter.check(
            key, limit=limit, window_seconds=window
        )
        assert allowed is True
        assert remaining == limit - (i + 1)
        assert retry_after is None

    # 4th request must fail
    allowed, remaining, reset_epoch, retry_after = await default_rate_limiter.check(
        key, limit=limit, window_seconds=window
    )
    assert allowed is False
    assert remaining == 0
    assert retry_after is not None
    assert retry_after > 0


class SimpleMockRedis:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def getdel(self, key: str) -> str | None:
        return self._data.pop(key, None)

    async def aclose(self) -> None:
        self._data.clear()


@pytest.mark.asyncio
async def test_endpoint_rate_limiting_returns_429():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    mock_redis = SimpleMockRedis()
    settings = Settings(
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        rate_limit_enabled=True,
    )
    app = create_app(settings)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    def override_redis() -> SimpleMockRedis:
        return mock_redis

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        # Test ticket exchange endpoint which has rate limit = 15
        for _ in range(15):
            resp = await client.post(
                "/api/v1/auth/exchange-desktop-ticket",
                json={"ticket": "invalid-dummy-ticket"},
                headers={"X-Forwarded-For": "192.168.1.50"},
            )
            assert "X-RateLimit-Limit" in resp.headers
            assert resp.headers["X-RateLimit-Limit"] == "15"

        # 16th request from same IP should get HTTP 429
        blocked_resp = await client.post(
            "/api/v1/auth/exchange-desktop-ticket",
            json={"ticket": "invalid-dummy-ticket"},
            headers={"X-Forwarded-For": "192.168.1.50"},
        )
        assert blocked_resp.status_code == 429
        data = blocked_resp.json()
        assert "error" in data
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in blocked_resp.headers
        assert int(blocked_resp.headers["Retry-After"]) > 0
        assert blocked_resp.headers["X-RateLimit-Remaining"] == "0"

        # Request from a different IP should be allowed (not rate limited)
        other_ip_resp = await client.post(
            "/api/v1/auth/exchange-desktop-ticket",
            json={"ticket": "invalid-dummy-ticket"},
            headers={"X-Forwarded-For": "192.168.1.99"},
        )
        # Should not be 429
        assert other_ip_resp.status_code != 429
        assert other_ip_resp.headers["X-RateLimit-Remaining"] == "14"

    await engine.dispose()
