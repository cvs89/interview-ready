from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeConnection:
    async def execute(self, _: Any) -> None:
        return None


class FakeEngine:
    @asynccontextmanager
    async def connect(self) -> AsyncIterator[FakeConnection]:
        yield FakeConnection()

    async def dispose(self) -> None:
        return None


class FakeRedis:
    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


def test_liveness_has_request_id() -> None:
    app = create_app(Settings(app_env="test"))
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "test-request"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "test-request"


def test_readiness_reports_healthy_dependencies() -> None:
    app = create_app(Settings(app_env="test"))
    with TestClient(app) as client:
        app.state.db_engine = FakeEngine()
        app.state.redis = FakeRedis()
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}
