from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.notification import TaskProcessRequest, TaskProcessResponse
from app.services.backend import TaskService

tasks_router = APIRouter(prefix="/internal/tasks", tags=["internal-tasks"])

Session = Annotated[AsyncSession, Depends(get_session)]


@tasks_router.post(
    "/process",
    response_model=TaskProcessResponse,
    status_code=status.HTTP_200_OK,
)
async def process_task(
    request: TaskProcessRequest,
    session: Session,
    raw_request: Request,
) -> TaskProcessResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    if settings and settings.database_backend == "firestore":
        from app.core.auth import get_current_user
        from app.firestore_backend.common import require_admin

        user = await get_current_user(
            raw_request, session, raw_request.headers.get("authorization")
        )
        require_admin(user)
    return await TaskService(session, settings=settings).process_task(
        task_type=request.task_type,
        payload=request.payload,
    )
