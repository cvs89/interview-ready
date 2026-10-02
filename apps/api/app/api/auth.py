from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.session import get_session
from app.integrations.redis import get_redis
from app.models.identity import User
from app.schemas.identity import UserResponse
from app.schemas.sessions import (
    ExchangeDesktopTicketRequest,
    ExchangeDesktopTicketResponse,
    MintDesktopTicketRequest,
    MintDesktopTicketResponse,
)
from app.services.sessions import DesktopAuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
RedisClient = Annotated[Redis, Depends(get_redis)]


@router.get("/me", response_model=UserResponse)
async def current_user(user: CurrentUser) -> User:
    return user


@router.post(
    "/mint-desktop-ticket",
    response_model=MintDesktopTicketResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(action="mint_desktop_ticket", limit=10, window_seconds=60))],
)
async def mint_desktop_ticket(
    request: MintDesktopTicketRequest,
    user: CurrentUser,
    session: Session,
    redis: RedisClient,
    raw_request: Request,
) -> MintDesktopTicketResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    return await DesktopAuthService(session, settings=settings).mint_desktop_ticket(
        user=user, request=request, redis=redis
    )


@router.post(
    "/exchange-desktop-ticket",
    response_model=ExchangeDesktopTicketResponse,
    dependencies=[
        Depends(RateLimiter(action="exchange_desktop_ticket", limit=15, window_seconds=60))
    ],
)
async def exchange_desktop_ticket(
    request: ExchangeDesktopTicketRequest,
    session: Session,
    redis: RedisClient,
    raw_request: Request,
) -> ExchangeDesktopTicketResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    return await DesktopAuthService(session, settings=settings).exchange_desktop_ticket(
        request=request, redis=redis
    )
