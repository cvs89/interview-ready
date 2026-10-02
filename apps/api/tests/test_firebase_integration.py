from typing import Any

import pytest

import app.integrations.firebase as firebase_module


@pytest.mark.asyncio
async def test_verification_checks_revocation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(firebase_module, "_ensure_firebase_app", lambda: None)

    def fake_verify(token: str, *, check_revoked: bool) -> dict[str, Any]:
        assert token == "firebase-token"
        assert check_revoked is True
        return {"uid": "firebase-user"}

    monkeypatch.setattr(firebase_module.auth, "verify_id_token", fake_verify)
    claims = await firebase_module.verify_firebase_id_token("firebase-token")
    assert claims == {"uid": "firebase-user"}
