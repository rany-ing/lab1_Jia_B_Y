from datetime import datetime, timedelta, timezone
from typing import Any

import redis
from celery import Task
from sqlalchemy import select

from app.celery_app import celery_app, is_shutting_down
from app.config import settings
from app.database import SessionLocal
from app.models.news import News
from app.models.user import User
from app.utils.logger import get_notification_logger

logger = get_notification_logger()


class GracefulShutdownRetry(Exception):
    """Raised when a worker receives a shutdown signal mid-batch so the task can be retried."""


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def _acquire_idempotency_key(redis_client: redis.Redis, key: str) -> bool:
    return bool(
        redis_client.set(
            key,
            "sent",
            nx=True,
            ex=settings.notification_idempotency_ttl_seconds,
        )
    )


def _release_idempotency_key(redis_client: redis.Redis, key: str) -> None:
    redis_client.delete(key)


@celery_app.task(
    bind=True,
    name="app.tasks.notifications.send_new_news_notification",
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def send_new_news_notification(self: Task, news_id: int) -> dict[str, Any]:
    task_id = self.request.id or "local"
    logger.info("Starting new_news notification task_id=%s for news_id=%s (attempt=%s)", task_id, news_id, self.request.retries + 1)

    db = SessionLocal()
    redis_client = get_redis_client()
    sent_count = 0
    skipped_count = 0

    try:
        news = db.get(News, news_id)
        if news is None:
            logger.warning("Task task_id=%s skipped: news_id=%s not found", task_id, news_id)
            return {"status": "not_found", "news_id": news_id, "sent": 0, "skipped": 0}

        users = list(db.scalars(select(User).order_by(User.id)).all())
        for user in users:
            if is_shutting_down():
                logger.warning(
                    "Graceful shutdown requested during task_id=%s (news_id=%s); re-queueing remaining users.",
                    task_id,
                    news_id,
                )
                raise GracefulShutdownRetry("Worker shutting down mid-batch")

            idempotency_key = f"notif:new_news:{news_id}:user:{user.id}"
            if not _acquire_idempotency_key(redis_client, idempotency_key):
                skipped_count += 1
                logger.info(
                    "[IDEMPOTENT SKIP] type=new_news | news_id=%s | to=%s (user_id=%s) | task_id=%s",
                    news_id,
                    user.email,
                    user.id,
                    task_id,
                )
                continue

            try:
                logger.info(
                    '[EMAIL MOCK] type=new_news | news_id=%s | title="%s" | to=%s (user_id=%s, name="%s") | task_id=%s',
                    news.id,
                    news.title,
                    user.email,
                    user.id,
                    user.name,
                    task_id,
                )
                sent_count += 1
            except Exception:
                _release_idempotency_key(redis_client, idempotency_key)
                raise

        return {
            "status": "completed",
            "news_id": news_id,
            "sent": sent_count,
            "skipped": skipped_count,
        }
    except Exception as exc:
        logger.error(
            "Task task_id=%s (news_id=%s) failed on attempt %s: %s",
            task_id,
            news_id,
            self.request.retries + 1,
            exc,
        )
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.notifications.send_weekly_digest",
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def send_weekly_digest(self: Task, digest_key: str | None = None) -> dict[str, Any]:
    task_id = self.request.id or "local"
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    period_key = digest_key or now.strftime("%Y-W%W")

    logger.info(
        "Starting weekly_digest task_id=%s for period=%s (attempt=%s)",
        task_id,
        period_key,
        self.request.retries + 1,
    )

    db = SessionLocal()
    redis_client = get_redis_client()
    sent_count = 0
    skipped_count = 0

    try:
        recent_news = list(
            db.scalars(
                select(News)
                .where(News.published_at >= week_ago)
                .order_by(News.published_at.desc())
            ).all()
        )
        if not recent_news:
            logger.info(
                "Weekly digest task_id=%s period=%s skipped: no news published in the last 7 days.",
                task_id,
                period_key,
            )
            return {
                "status": "no_news",
                "period": period_key,
                "news_count": 0,
                "sent": 0,
                "skipped": 0,
            }

        news_ids = [n.id for n in recent_news]
        news_titles = "; ".join(f'"{n.title}"' for n in recent_news)
        users = list(db.scalars(select(User).order_by(User.id)).all())

        for user in users:
            if is_shutting_down():
                logger.warning(
                    "Graceful shutdown requested during weekly_digest task_id=%s (period=%s); re-queueing remaining users.",
                    task_id,
                    period_key,
                )
                raise GracefulShutdownRetry("Worker shutting down mid-batch")

            idempotency_key = f"notif:weekly_digest:{period_key}:user:{user.id}"
            if not _acquire_idempotency_key(redis_client, idempotency_key):
                skipped_count += 1
                logger.info(
                    "[IDEMPOTENT SKIP] type=weekly_digest | period=%s | to=%s (user_id=%s) | task_id=%s",
                    period_key,
                    user.email,
                    user.id,
                    task_id,
                )
                continue

            try:
                logger.info(
                    '[EMAIL MOCK] type=weekly_digest | period=%s | news_count=%s | news_ids=%s | titles=[%s] | to=%s (user_id=%s, name="%s") | task_id=%s',
                    period_key,
                    len(recent_news),
                    news_ids,
                    news_titles,
                    user.email,
                    user.id,
                    user.name,
                    task_id,
                )
                sent_count += 1
            except Exception:
                _release_idempotency_key(redis_client, idempotency_key)
                raise

        return {
            "status": "completed",
            "period": period_key,
            "news_count": len(recent_news),
            "sent": sent_count,
            "skipped": skipped_count,
        }
    except Exception as exc:
        logger.error(
            "Weekly digest task_id=%s (period=%s) failed on attempt %s: %s",
            task_id,
            period_key,
            self.request.retries + 1,
            exc,
        )
        raise
    finally:
        db.close()
