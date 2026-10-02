from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import admin_router as operations_admin_router
from app.api.audit import audit_router
from app.api.auth import router as auth_router
from app.api.bookings import bookings_router, payments_router, webhooks_router
from app.api.feedback import feedback_router, reviews_router
from app.api.health import router as health_router
from app.api.interviewers import admin_router as interviewers_admin_router
from app.api.interviewers import router as interviewers_router
from app.api.notifications import notifications_router
from app.api.tasks import tasks_router
from app.core.config import Settings, get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.db.session import create_database_engine, create_session_factory
from app.integrations.redis import create_redis_client


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.db_engine = create_database_engine(
            app_settings.database_url,
            pool_size=app_settings.db_pool_size,
            max_overflow=app_settings.db_max_overflow,
            pool_timeout=app_settings.db_pool_timeout,
            pool_recycle=app_settings.db_pool_recycle,
            pool_pre_ping=app_settings.db_pool_pre_ping,
        )
        app.state.session_factory = create_session_factory(app.state.db_engine)
        app.state.redis = create_redis_client(app_settings.redis_url)
        yield
        await app.state.redis.aclose()
        await app.state.db_engine.dispose()

    app = FastAPI(title=app_settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.web_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_exception_handlers(app)

    # Base endpoints
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(interviewers_router)
    app.include_router(interviewers_admin_router)
    app.include_router(operations_admin_router)
    app.include_router(bookings_router)
    app.include_router(payments_router)
    app.include_router(webhooks_router)
    app.include_router(feedback_router)
    app.include_router(reviews_router)
    app.include_router(notifications_router)
    app.include_router(audit_router)
    app.include_router(tasks_router)

    # API v1 prefix routes
    api_v1_router = APIRouter(prefix="/api/v1")
    api_v1_router.include_router(auth_router)
    api_v1_router.include_router(interviewers_router)
    api_v1_router.include_router(interviewers_admin_router)
    api_v1_router.include_router(operations_admin_router)
    api_v1_router.include_router(bookings_router)
    api_v1_router.include_router(payments_router)
    api_v1_router.include_router(webhooks_router)
    api_v1_router.include_router(feedback_router)
    api_v1_router.include_router(reviews_router)
    api_v1_router.include_router(notifications_router)
    api_v1_router.include_router(audit_router)
    api_v1_router.include_router(tasks_router)
    app.include_router(api_v1_router)

    return app


app = create_app()
