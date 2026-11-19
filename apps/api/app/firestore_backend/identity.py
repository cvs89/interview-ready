from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.common import BaseService, key_for, new_doc, now, user_model
from app.firestore_backend.store import UnitOfWork
from app.models.identity import User
from app.services.identity import Identity


class IdentityService(BaseService):
    async def authenticate(self, claims: dict[str, Any]) -> User:
        identity = Identity.from_verified_token(claims)

        async def operation(tx: UnitOfWork) -> User:
            uid_key = key_for(identity.firebase_uid)
            email_key = key_for(identity.email)
            binding = await tx.get("identity_keys", uid_key)
            email_owner = await tx.get("email_keys", email_key)
            document = await tx.get("users", binding["user_id"]) if binding else None
            if email_owner and (not document or email_owner["user_id"] != document["id"]):
                raise ApiError("IDENTITY_CONFLICT", "Email belongs to another account.", 409)
            if document and document["status"] != "ACTIVE":
                raise ApiError(f"ACCOUNT_{document['status']}", "Account is not active.", 403)
            if document is None:
                document = new_doc(
                    firebase_uid=identity.firebase_uid,
                    email=identity.email,
                    full_name=identity.full_name,
                    role="CANDIDATE",
                    status="ACTIVE",
                    email_verified=identity.email_verified,
                    auth_provider=identity.auth_provider,
                    last_login_at=now(),
                )
            # Never trust role claims; admin bootstrap also requires verified email.
            if identity.email_verified and identity.email in self.settings.admin_emails:
                document["role"] = "ADMIN"
            document.update(
                email_verified=identity.email_verified,
                auth_provider=identity.auth_provider,
                last_login_at=now(),
                updated_at=now(),
            )
            tx.put("users", document["id"], document)
            tx.put("identity_keys", uid_key, {"user_id": document["id"]})
            tx.put("email_keys", email_key, {"user_id": document["id"]})
            return user_model(document)

        return await self.store.run(operation)
