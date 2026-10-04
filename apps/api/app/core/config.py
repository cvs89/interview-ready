from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Interview Ready API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = (
        "postgresql+asyncpg://interview_ready:local_only_password@localhost:5432/interview_ready"
    )
    redis_url: str = "redis://localhost:6379/0"
    web_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    admin_emails: Annotated[list[str], NoDecode] = ["narukakomal27@gmail.com"]
    reservation_ttl_minutes: int = 10
    webhook_signing_secret: str = "local_dev_webhook_signing_secret"
    payment_provider: str = "mock"
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None

    # Module 05: Desktop ticket, Session JWT, and LiveKit configuration
    desktop_ticket_ttl_seconds: int = 60
    join_window_lead_minutes: int = 10
    join_window_grace_minutes: int = 30
    session_jwt_secret: str = "dev_session_jwt_signing_secret_do_not_use_in_prod"
    session_jwt_ttl_seconds: int = 7200
    livekit_url: str = "wss://livekit.interviewready.local"
    livekit_api_key: str = "dev_livekit_api_key"
    livekit_api_secret: str = "dev_livekit_api_secret_do_not_use_in_prod"
    livekit_token_ttl_seconds: int = 7200

    # Module 12: Production Cloud SQL pooling and Storage settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_pool_pre_ping: bool = True

    # Module 13: Rate limiting and Security baseline
    rate_limit_enabled: bool = True
    rate_limit_mint_ticket_limit: int = 10
    rate_limit_exchange_ticket_limit: int = 15
    rate_limit_reservation_limit: int = 10
    rate_limit_checkout_limit: int = 10
    rate_limit_search_limit: int = 60
    rate_limit_window_seconds: int = 60

    gcp_project_id: str | None = None
    gcs_bucket_name: str | None = None
    gcs_signed_url_ttl_seconds: int = 3600
    gemini_api_key: str | None = None

    @field_validator("web_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("admin_emails", mode="before")
    @classmethod
    def parse_admin_emails(cls, value: object) -> object:
        if isinstance(value, str) and not value.startswith("["):
            return [email.strip().casefold() for email in value.split(",") if email.strip()]
        if isinstance(value, list):
            return [str(e).strip().casefold() for e in value if str(e).strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
