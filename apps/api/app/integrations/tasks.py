import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class TaskQueue(ABC):
    @abstractmethod
    async def enqueue_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        schedule_time: datetime | None = None,
    ) -> str:
        pass


class MockTaskQueue(TaskQueue):
    def __init__(self) -> None:
        self.enqueued_tasks: list[dict[str, Any]] = []

    async def enqueue_task(
        self,
        task_type: str,
        payload: dict[str, Any],
        schedule_time: datetime | None = None,
    ) -> str:
        task_id = f"task_{uuid.uuid4()}"
        self.enqueued_tasks.append(
            {
                "task_id": task_id,
                "task_type": task_type,
                "payload": payload,
                "schedule_time": schedule_time,
            }
        )
        return task_id
