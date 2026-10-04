import pytest

from app.core.config import Settings


def test_comma_separated_web_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEB_ORIGINS", "http://localhost:3000,https://example.com")
    settings = Settings()
    assert settings.web_origins == ["http://localhost:3000", "https://example.com"]


def test_comma_separated_admin_emails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_EMAILS", "Admin1@example.com, admin2@example.com ")
    settings = Settings()
    assert settings.admin_emails == ["admin1@example.com", "admin2@example.com"]

