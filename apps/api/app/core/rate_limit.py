import asyncio
import time
import uuid
from typing import Annotated

import structlog
from fastapi import Depends, Request, Response
from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.integrations.redis import get_redis

logger = structlog.get_logger()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._memory_store: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def reset_memory(self) -> None:
        self._memory_store.clear()

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        redis: Redis | None = None,
    ) -> tuple[bool, int, int, int | None]:
        """Check rate limit for key.

        Returns:
            (allowed, remaining, reset_epoch, retry_after)
        """
        now = time.time()
        window_start = now - window_seconds
        reset_epoch = int(now + window_seconds)

        # 1. Try Redis sliding window if available
        if redis is not None:
            try:
                unique_member = f"{now:.6f}:{uuid.uuid4().hex}"
                pipe = redis.pipeline()
                pipe.zremrangebyscore(key, "-inf", window_start)
                pipe.zcard(key)
                pipe.zadd(key, {unique_member: now})
                pipe.expire(key, window_seconds + 5)
                results = await pipe.execute()

                current_count = int(results[1])
                if current_count >= limit:
                    await redis.zrem(key, unique_member)
                    oldest = await redis.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        retry_after = max(1, int(oldest[0][1] + window_seconds - now))
                    else:
                        retry_after = window_seconds
                    return False, 0, reset_epoch, retry_after

                remaining = max(0, limit - (current_count + 1))
                return True, remaining, reset_epoch, None
            except Exception as e:
                logger.warning("redis_rate_limit_fallback_to_memory", error=str(e), key=key)

        # 2. In-memory sliding window fallback
        async with self._lock:
            timestamps = self._memory_store.get(key, [])
            timestamps = [t for t in timestamps if t > window_start]
            if len(timestamps) >= limit:
                retry_after = max(1, int(timestamps[0] + window_seconds - now))
                self._memory_store[key] = timestamps
                return False, 0, reset_epoch, retry_after

            timestamps.append(now)
            self._memory_store[key] = timestamps
            remaining = max(0, limit - len(timestamps))
            return True, remaining, reset_epoch, None


default_rate_limiter = SlidingWindowRateLimiter()


class RateLimiter:
    def __init__(
        self,
        action: str,
        limit: int = 60,
        window_seconds: int = 60,
        use_user_id: bool = True,
    ) -> None:
        self.action = action
        self.limit = limit
        self.window_seconds = window_seconds
        self.use_user_id = use_user_id

    async def __call__(
        self,
        request: Request,
        response: Response,
        settings: Annotated[Settings, Depends(get_settings)],
        redis: Annotated[Redis | None, Depends(get_redis)] = None,
    ) -> None:
        if not settings.rate_limit_enabled:
            return

        user = getattr(request.state, "user", None)
        if self.use_user_id and user is not None and getattr(user, "id", None) is not None:
            identifier = f"u:{user.id}"
        else:
            identifier = f"ip:{get_client_ip(request)}"

        key = f"ratelimit:{self.action}:{identifier}"
        allowed, remaining, reset_epoch, retry_after = await default_rate_limiter.check(
            key=key,
            limit=self.limit,
            window_seconds=self.window_seconds,
            redis=redis,
        )

        rate_limit_headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_epoch),
        }
        request.state.rate_limit_headers = rate_limit_headers
        for k, v in rate_limit_headers.items():
            response.headers[k] = v

        if not allowed:
            retry_val = str(retry_after or self.window_seconds)
            raise ApiError(
                code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please try again later.",
                status_code=429,
                headers={
                    "Retry-After": retry_val,
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                },
            )
