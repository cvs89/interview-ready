import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_security_headers_present_on_responses():
    settings = Settings(
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
    )
    app = create_app(settings)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        resp = await client.get("/health/live")
        assert resp.status_code == 200

        # Verify all security headers
        headers = resp.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
        assert "camera=()" in headers.get("Permissions-Policy", "")
        assert headers.get("Cross-Origin-Opener-Policy") == "same-origin"
        assert headers.get("Cross-Origin-Resource-Policy") == "same-site"
        assert "default-src 'none'" in headers.get("Content-Security-Policy", "")
        assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy", "")
