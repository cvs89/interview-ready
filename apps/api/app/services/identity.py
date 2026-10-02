from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.identity import User, UserStatus
from app.repositories.users import UserRepository


@dataclass(frozen=True, slots=True)
class Identity:
    firebase_uid: str
    email: str
    full_name: str
    email_verified: bool
    auth_provider: str | None

    @classmethod
    def from_verified_token(cls, claims: dict[str, Any]) -> "Identity":
        uid = claims.get("uid") or claims.get("sub")
        email = claims.get("email")
        if not isinstance(uid, str) or not uid.strip():
            raise ApiError("INVALID_TOKEN", "The authentication token is invalid.", 401)
        if not isinstance(email, str) or "@" not in email:
            raise ApiError("EMAIL_REQUIRED", "A valid email claim is required.", 401)

        normalized_email = email.strip().casefold()
        name = claims.get("name")
        full_name = name.strip() if isinstance(name, str) and name.strip() else email.split("@")[0]
        firebase_claims = claims.get("firebase")
        provider = None
        if isinstance(firebase_claims, dict):
            candidate = firebase_claims.get("sign_in_provider")
            provider = candidate if isinstance(candidate, str) else None
        return cls(
            firebase_uid=uid,
            email=normalized_email,
            full_name=full_name,
            email_verified=claims.get("email_verified") is True,
            auth_provider=provider,
        )


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def authenticate(self, claims: dict[str, Any]) -> User:
        identity = Identity.from_verified_token(claims)
        user = await self.users.get_by_firebase_uid(identity.firebase_uid)
        if user is not None:
            if user.status == UserStatus.DISABLED:
                raise ApiError("ACCOUNT_DISABLED", "This account has been disabled.", 403)
            if user.status == UserStatus.SUSPENDED:
                raise ApiError("ACCOUNT_SUSPENDED", "This account has been suspended.", 403)
            self.users.update_login_metadata(
                user,
                email_verified=identity.email_verified,
                auth_provider=identity.auth_provider,
            )
            return await self.users.commit_and_refresh(user)

        email_owner = await self.users.get_by_email(identity.email)
        if email_owner is not None:
            raise ApiError(
                "IDENTITY_CONFLICT",
                "This email is already associated with another account.",
                409,
            )

        user = self.users.create_candidate(
            firebase_uid=identity.firebase_uid,
            email=identity.email,
            full_name=identity.full_name,
            email_verified=identity.email_verified,
            auth_provider=identity.auth_provider,
        )
        try:
            return await self.users.commit_and_refresh(user)
        except IntegrityError:
            await self.session.rollback()
            concurrent_user = await self.users.get_by_firebase_uid(identity.firebase_uid)
            if concurrent_user is None:
                raise ApiError(
                    "IDENTITY_CONFLICT",
                    "The account could not be registered safely.",
                    409,
                ) from None
            return concurrent_user
