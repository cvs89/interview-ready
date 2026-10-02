import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any, TypeAlias

import httpx
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.auth as auth_module
from app.core.auth import ensure_owner_or_role, require_role, require_verified_email
from app.core.config import Settings
from app.core.errors import ApiError
from app.db.base import Base
from app.db.session import get_session
from app.integrations.firebase import FirebaseTokenInvalid, FirebaseUserDisabled
from app.main import create_app
from app.models.identity import User, UserRole

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]
AuthContext: TypeAlias = tuple[httpx.AsyncClient, SessionFactory, dict[str, Any]]


@pytest_asyncio.fixture
async def auth_context(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[AuthContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    app = create_app(Settings(app_env="test"))

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    claims: dict[str, Any] = {
        "uid": "firebase-user-1",
        "email": "Candidate@Example.com",
        "name": "Candidate One",
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
        "role": "ADMIN",
    }

    async def fake_verifier(token: str) -> dict[str, Any]:
        if token == "invalid":
            raise FirebaseTokenInvalid
        if token == "disabled":
            raise FirebaseUserDisabled
        return claims

    app.dependency_overrides[get_session] = override_session
    monkeypatch.setattr(auth_module, "verify_firebase_id_token", fake_verifier)
    install_guard_test_routes(app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, claims
    await engine.dispose()


def install_guard_test_routes(app: FastAPI) -> None:
    @app.get("/_test/admin")
    async def admin_only(
        user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    ) -> dict[str, str]:
        return {"role": user.role.value}

    @app.get("/_test/verified")
    async def verified_only(
        user: Annotated[User, Depends(require_verified_email)],
    ) -> dict[str, bool]:
        return {"email_verified": user.email_verified}


@pytest.mark.asyncio
async def test_missing_token_returns_error_envelope(auth_context: AuthContext) -> None:
    client, _, _ = auth_context
    response = await client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert response.json()["error"]["request_id"]


@pytest.mark.asyncio
async def test_malformed_token_is_rejected(auth_context: AuthContext) -> None:
    client, _, _ = auth_context
    response = await client.get("/auth/me", headers={"Authorization": "Token nonsense"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MALFORMED_AUTHORIZATION"


@pytest.mark.asyncio
async def test_invalid_and_disabled_tokens_are_rejected(auth_context: AuthContext) -> None:
    client, _, _ = auth_context
    invalid = await client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    disabled = await client.get("/auth/me", headers={"Authorization": "Bearer disabled"})
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "INVALID_TOKEN"
    assert disabled.status_code == 403
    assert disabled.json()["error"]["code"] == "USER_DISABLED"


@pytest.mark.asyncio
async def test_first_login_creates_candidate_from_verified_claims(
    auth_context: AuthContext,
) -> None:
    client, session_factory, _ = auth_context
    response = await client.get("/auth/me", headers={"Authorization": "Bearer valid"})
    assert response.status_code == 200
    assert response.json()["email"] == "candidate@example.com"
    assert response.json()["role"] == "CANDIDATE"

    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()
        assert user.firebase_uid == "firebase-user-1"
        assert user.role is UserRole.CANDIDATE
        assert user.last_login_at is not None


@pytest.mark.asyncio
async def test_repeated_login_does_not_duplicate_user(auth_context: AuthContext) -> None:
    client, session_factory, _ = auth_context
    headers = {"Authorization": "Bearer valid"}
    first = await client.get("/auth/me", headers=headers)
    second = await client.get("/auth/me", headers=headers)
    assert first.json()["id"] == second.json()["id"]

    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(User))
        assert count == 1


@pytest.mark.asyncio
async def test_role_enforcement_and_role_persistence(auth_context: AuthContext) -> None:
    client, session_factory, _ = auth_context
    headers = {"Authorization": "Bearer valid"}
    denied = await client.get("/_test/admin", headers=headers)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"

    async with session_factory() as session:
        user = (await session.execute(select(User))).scalar_one()
        user.role = UserRole.ADMIN
        await session.commit()

    allowed = await client.get("/_test/admin", headers=headers)
    assert allowed.status_code == 200
    assert allowed.json() == {"role": "ADMIN"}


@pytest.mark.asyncio
async def test_unverified_email_guard(auth_context: AuthContext) -> None:
    client, _, claims = auth_context
    claims["uid"] = "unverified-user"
    claims["email"] = "unverified@example.com"
    claims["email_verified"] = False
    response = await client.get("/_test/verified", headers={"Authorization": "Bearer unverified"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


@pytest.mark.asyncio
async def test_email_collision_is_not_silently_linked(auth_context: AuthContext) -> None:
    client, _, claims = auth_context
    headers = {"Authorization": "Bearer valid"}
    assert (await client.get("/auth/me", headers=headers)).status_code == 200
    claims["uid"] = "different-firebase-user"
    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDENTITY_CONFLICT"


def test_firebase_uid_is_not_database_primary_key() -> None:
    user = User(
        firebase_uid="firebase-uid",
        email="person@example.com",
        full_name="Person",
    )
    assert isinstance(user.id, (uuid.UUID, type(None)))
    assert User.__table__.primary_key.columns.keys() == ["id"]


def test_ownership_guard_allows_owner_or_admin_only() -> None:
    owner_id = uuid.uuid4()
    candidate = User(
        id=uuid.uuid4(),
        firebase_uid="candidate",
        email="candidate@example.com",
        full_name="Candidate",
        role=UserRole.CANDIDATE,
    )
    with pytest.raises(ApiError) as denied:
        ensure_owner_or_role(owner_id, candidate, UserRole.ADMIN)
    assert denied.value.code == "FORBIDDEN"

    candidate.id = owner_id
    ensure_owner_or_role(owner_id, candidate, UserRole.ADMIN)

    candidate.id = uuid.uuid4()
    candidate.role = UserRole.ADMIN
    ensure_owner_or_role(owner_id, candidate, UserRole.ADMIN)
