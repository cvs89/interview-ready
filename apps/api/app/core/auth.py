import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.db.session import get_session
from app.integrations.firebase import (
    FirebaseTokenInvalid,
    FirebaseUserDisabled,
    verify_firebase_id_token,
)
from app.models.identity import User, UserRole
from app.services.identity import IdentityService

CurrentUserDependency = Callable[..., Coroutine[Any, Any, User]]


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise ApiError("AUTHENTICATION_REQUIRED", "Authentication is required.", 401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].casefold() != "bearer" or not parts[1]:
        raise ApiError("MALFORMED_AUTHORIZATION", "The authorization header is malformed.", 401)
    return parts[1]


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    token = _extract_bearer_token(authorization)
    try:
        claims = await verify_firebase_id_token(token)
    except FirebaseUserDisabled:
        raise ApiError("USER_DISABLED", "This account has been disabled.", 403) from None
    except FirebaseTokenInvalid:
        raise ApiError("INVALID_TOKEN", "The authentication token is invalid.", 401) from None
    user = await IdentityService(session).authenticate(claims)
    request.state.user = user
    return user


def require_role(*allowed_roles: UserRole) -> CurrentUserDependency:
    if not allowed_roles:
        raise ValueError("At least one role is required")

    async def role_dependency(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if user.role not in allowed_roles:
            raise ApiError("FORBIDDEN", "You do not have permission for this action.", 403)
        return user

    return role_dependency


async def require_verified_email(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.email_verified:
        raise ApiError("EMAIL_NOT_VERIFIED", "A verified email is required.", 403)
    return user


def ensure_owner_or_role(
    resource_owner_id: uuid.UUID,
    current_user: User,
    *allowed_roles: UserRole,
) -> None:
    if current_user.id != resource_owner_id and current_user.role not in allowed_roles:
        raise ApiError("FORBIDDEN", "You do not have permission for this resource.", 403)
