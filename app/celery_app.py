import threading

from celery import Celery
from celery.schedules import crontab
from celery.signals import worker_shutdown, worker_shutting_down

from app.config import settings
from app.utils.logger import get_notification_logger

logger = get_notification_logger()

_shutdown_event = threading.Event()


def is_shutting_down() -> bool:
    return _shutdown_event.is_set()


def reset_shutdown_flag() -> None:
    _shutdown_event.clear()


celery_app = Celery(
    "news_notifications",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.notifications"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.celery_task_always_eager,
    # Graceful shutdown & reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": 3600},
    # Weekly digest every Sunday at 09:00 UTC
    beat_schedule={
        "weekly-news-digest": {
            "task": "app.tasks.notifications.send_weekly_digest",
            "schedule": crontab(hour=9, minute=0, day_of_week="sunday"),
        }
    },
)


@worker_shutting_down.connect
def handle_worker_shutting_down(sig: str | None = None, how: str | None = None, exitcode: int | None = None, **kwargs: object) -> None:
    _shutdown_event.set()
    logger.warning(
        "Celery worker graceful shutdown initiated (sig=%s, how=%s, exitcode=%s)",
        sig,
        how,
        exitcode,
    )


@worker_shutdown.connect
def handle_worker_shutdown(**kwargs: object) -> None:
    _shutdown_event.set()
    logger.info("Celery worker shutdown completed cleanly.")
