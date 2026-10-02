from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=None)
async def readiness(request: Request) -> dict[str, Any] | JSONResponse:
    checks: dict[str, str] = {}
    try:
        async with request.app.state.db_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        await request.app.state.redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    ready = all(value == "ok" for value in checks.values())
    payload = {"status": "ready" if ready else "not_ready", "checks": checks}
    return payload if ready else JSONResponse(status_code=503, content=payload)
