import hashlib
import json
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Request
from redis.asyncio import Redis


def create_redis_client(redis_url: str) -> Redis:
    return cast(Redis, Redis.from_url(redis_url, decode_responses=True))


def get_redis(request: Request) -> Redis | None:
    return getattr(request.app.state, "redis", None)


class DesktopTicketStore:
    KEY_PREFIX = "desktop_ticket:"

    @classmethod
    def _hash_ticket(cls, ticket: str) -> str:
        return hashlib.sha256(ticket.encode("utf-8")).hexdigest()

    @classmethod
    async def mint_ticket(
        cls,
        redis: Redis,
        *,
        user_id: uuid.UUID,
        booking_id: uuid.UUID,
        role: str,
        ttl_seconds: int = 60,
    ) -> str:
        # Cryptographically secure random token (256 bits = 32 bytes)
        raw_ticket = secrets.token_urlsafe(32)
        ticket_hash = cls._hash_ticket(raw_ticket)
        redis_key = f"{cls.KEY_PREFIX}{ticket_hash}"

        payload = {
            "user_id": str(user_id),
            "booking_id": str(booking_id),
            "role": role,
            "nonce": secrets.token_hex(16),
            "issued_at": datetime.now(UTC).isoformat(),
        }

        await redis.set(redis_key, json.dumps(payload), ex=ttl_seconds)
        return raw_ticket

    @classmethod
    async def exchange_ticket(
        cls,
        redis: Redis,
        raw_ticket: str,
    ) -> dict[str, Any] | None:
        ticket_hash = cls._hash_ticket(raw_ticket)
        redis_key = f"{cls.KEY_PREFIX}{ticket_hash}"

        # Atomic GETDEL ensures one-time consumption
        try:
            raw_data = await redis.getdel(redis_key)
        except Exception:
            # Lua fallback for older Redis or mock drivers without getdel
            lua = """
            local val = redis.call('GET', KEYS[1])
            if val then
                redis.call('DEL', KEYS[1])
            end
            return val
            """
            eval_result = redis.eval(lua, 1, redis_key)
            raw_data = await cast(Any, eval_result)

        if not raw_data:
            return None

        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")

        return cast(dict[str, Any], json.loads(raw_data))
