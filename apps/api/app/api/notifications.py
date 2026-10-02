import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.identity import User
from app.schemas.notification import InAppNotificationResponse
from app.services.notification import NotificationService

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@notifications_router.get("/me", response_model=list[InAppNotificationResponse])
async def list_notifications(
    user: CurrentUser,
    session: Session,
    unread_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[InAppNotificationResponse]:
    return await NotificationService(session).list_in_app_notifications(
        user=user,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@notifications_router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
) -> dict[str, bool]:
    updated = await NotificationService(session).mark_as_read(user, notification_id)
    return {"success": updated}


@notifications_router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
)
async def mark_all_notifications_read(
    user: CurrentUser,
    session: Session,
) -> dict[str, int]:
    count = await NotificationService(session).mark_all_as_read(user)
    return {"marked_count": count}
