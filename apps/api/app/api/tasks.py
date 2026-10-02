from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.notification import TaskProcessRequest, TaskProcessResponse
from app.services.tasks import TaskService

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
    return await TaskService(session, settings=settings).process_task(
        task_type=request.task_type,
        payload=request.payload,
    )
