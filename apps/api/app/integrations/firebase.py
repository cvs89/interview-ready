from typing import Any, cast

import firebase_admin  # type: ignore[import-untyped]
from anyio import to_thread
from firebase_admin import auth


class FirebaseTokenInvalid(Exception):
    pass


class FirebaseUserDisabled(Exception):
    pass


def _ensure_firebase_app() -> None:
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()


def _verify_sync(token: str) -> dict[str, Any]:
    _ensure_firebase_app()
    try:
        return cast(dict[str, Any], auth.verify_id_token(token, check_revoked=True))
    except auth.UserDisabledError as exc:
        raise FirebaseUserDisabled from exc
    except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError) as exc:
        raise FirebaseTokenInvalid from exc
    except (ValueError, firebase_admin.exceptions.FirebaseError) as exc:
        raise FirebaseTokenInvalid from exc


async def verify_firebase_id_token(token: str) -> dict[str, Any]:
    return await to_thread.run_sync(_verify_sync, token)
