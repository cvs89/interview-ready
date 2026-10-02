import pytest

from app.core.config import Settings


def test_comma_separated_web_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_ORIGINS", "http://localhost:3000,https://example.com")
    settings = Settings()
    assert settings.web_origins == ["http://localhost:3000", "https://example.com"]
