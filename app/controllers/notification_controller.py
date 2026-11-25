from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Query, status
from pydantic import BaseModel

from app.celery_app import celery_app
from app.tasks.notifications import send_weekly_digest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class TaskQueuedResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Any = None


@router.post("/digest", response_model=TaskQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_weekly_digest(
    digest_key: str | None = Query(default=None, description="Optional idempotency key for the digest period"),
) -> TaskQueuedResponse:
    task = send_weekly_digest.delay(digest_key=digest_key)
    return TaskQueuedResponse(task_id=task.id, status="queued")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    async_result = AsyncResult(task_id, app=celery_app)
    return TaskStatusResponse(
        task_id=task_id,
        status=async_result.status,
        result=async_result.result if async_result.ready() else None,
    )
