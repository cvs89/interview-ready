import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import Settings, get_settings
from app.models.identity import User


class TokenError(Exception):
    pass


def create_session_jwt(
    *,
    user: User,
    booking_id: uuid.UUID,
    session_id: uuid.UUID,
    role: str,
    settings: Settings | None = None,
) -> str:
    app_settings = settings or get_settings()
    now = datetime.now(UTC)
    exp = now + timedelta(seconds=app_settings.session_jwt_ttl_seconds)

    payload = {
        "sub": str(user.id),
        "booking_id": str(booking_id),
        "session_id": str(session_id),
        "role": role,
        "user_role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "email": user.email,
        "name": user.full_name,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, app_settings.session_jwt_secret, algorithm="HS256")


def verify_session_jwt(
    token: str,
    settings: Settings | None = None,
) -> dict[str, Any]:
    app_settings = settings or get_settings()
    try:
        return jwt.decode(token, app_settings.session_jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired session token.") from exc


def create_livekit_token(
    *,
    user: User,
    room_name: str,
    booking_id: uuid.UUID,
    role: str,
    settings: Settings | None = None,
) -> str:
    app_settings = settings or get_settings()
    now = datetime.now(UTC)
    exp = now + timedelta(seconds=app_settings.livekit_token_ttl_seconds)

    metadata = json.dumps(
        {
            "user_id": str(user.id),
            "role": role,
            "booking_id": str(booking_id),
        }
    )

    payload = {
        "iss": app_settings.livekit_api_key,
        "sub": str(user.id),
        "name": user.full_name,
        "video": {
            "room": room_name,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
        "metadata": metadata,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, app_settings.livekit_api_secret, algorithm="HS256")
