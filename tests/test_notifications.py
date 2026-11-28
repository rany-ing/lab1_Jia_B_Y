from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.celery_app import (
    celery_app,
    handle_worker_shutting_down,
    is_shutting_down,
    reset_shutdown_flag,
)
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.news import News
from app.models.user import User
from app.tasks.notifications import (
    GracefulShutdownRetry,
    send_new_news_notification,
    send_weekly_digest,
)


@pytest.fixture()
def test_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def fake_redis():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture()
def isolated_log_file(tmp_path: Path, monkeypatch):
    log_file = tmp_path / "notifications.log"
    monkeypatch.setattr(settings, "notification_log_file", str(log_file))
    import logging

    from app.utils.logger import get_notification_logger

    logger = logging.getLogger("notifications")
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)
    get_notification_logger()
    return log_file


def _seed_users_and_news(SessionCls):
    db = SessionCls()
    try:
        u1 = User(name="Alice Author", email="alice@example.com", is_verified_author=True)
        u2 = User(name="Bob Reader", email="bob@example.com", is_verified_author=False)
        db.add_all([u1, u2])
        db.commit()
        db.refresh(u1)
        db.refresh(u2)

        recent_news = News(
            title="Fresh Release",
            content={"body": "Celery + Redis"},
            author_id=u1.id,
            published_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        old_news = News(
            title="Old News",
            content={"body": "Two weeks ago"},
            author_id=u1.id,
            published_at=datetime.now(timezone.utc) - timedelta(days=14),
        )
        db.add_all([recent_news, old_news])
        db.commit()
        db.refresh(recent_news)
        db.refresh(old_news)
        return u1.id, u2.id, recent_news.id, old_news.id
    finally:
        db.close()


def test_celery_config_beat_retries_and_graceful_shutdown():
    # Beat schedule for Sunday weekly digest
    schedule = celery_app.conf.beat_schedule["weekly-news-digest"]
    assert schedule["task"] == "app.tasks.notifications.send_weekly_digest"
    assert schedule["schedule"].day_of_week == {0}

    # Graceful shutdown worker settings
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1

    # Retry + exponential backoff settings on tasks
    for task in (send_new_news_notification, send_weekly_digest):
        assert task.max_retries == 5
        assert task.retry_backoff == 2
        assert task.retry_backoff_max == 300
        assert task.retry_jitter is True
        assert Exception in task.autoretry_for


def test_new_news_notification_idempotency_and_file_logging(test_db, fake_redis, isolated_log_file):
    _, _, recent_news_id, _ = _seed_users_and_news(test_db)

    with (
        patch("app.tasks.notifications.SessionLocal", test_db),
        patch("app.tasks.notifications.get_redis_client", return_value=fake_redis),
    ):
        res1 = send_new_news_notification.apply(args=(recent_news_id,)).get()
        assert res1["status"] == "completed"
        assert res1["sent"] == 2
        assert res1["skipped"] == 0

        # Second run must be idempotent (0 sent, 2 skipped)
        res2 = send_new_news_notification.apply(args=(recent_news_id,)).get()
        assert res2["status"] == "completed"
        assert res2["sent"] == 0
        assert res2["skipped"] == 2

    log_text = isolated_log_file.read_text(encoding="utf-8")
    assert log_text.count("[EMAIL MOCK] type=new_news") == 2
    assert "to=alice@example.com" in log_text
    assert "to=bob@example.com" in log_text
    assert 'title="Fresh Release"' in log_text


def test_weekly_digest_filters_last_7_days_and_idempotency(test_db, fake_redis, isolated_log_file):
    _seed_users_and_news(test_db)

    with (
        patch("app.tasks.notifications.SessionLocal", test_db),
        patch("app.tasks.notifications.get_redis_client", return_value=fake_redis),
    ):
        res1 = send_weekly_digest.apply(kwargs={"digest_key": "2026-W47"}).get()
        assert res1["status"] == "completed"
        assert res1["news_count"] == 1
        assert res1["sent"] == 2
        assert res1["skipped"] == 0

        res2 = send_weekly_digest.apply(kwargs={"digest_key": "2026-W47"}).get()
        assert res2["sent"] == 0
        assert res2["skipped"] == 2

    log_text = isolated_log_file.read_text(encoding="utf-8")
    assert log_text.count("[EMAIL MOCK] type=weekly_digest") == 2
    assert "Fresh Release" in log_text
    assert "Old News" not in log_text


def test_graceful_shutdown_interrupts_batch_cleanly(test_db, fake_redis, isolated_log_file):
    _, _, recent_news_id, _ = _seed_users_and_news(test_db)
    reset_shutdown_flag()
    handle_worker_shutting_down(sig="SIGTERM", how="warm", exitcode=0)
    assert is_shutting_down() is True

    try:
        with (
            patch("app.tasks.notifications.SessionLocal", test_db),
            patch("app.tasks.notifications.get_redis_client", return_value=fake_redis),
        ):
            with pytest.raises(GracefulShutdownRetry):
                send_new_news_notification.run(recent_news_id)
    finally:
        reset_shutdown_flag()


def test_fastapi_endpoints_trigger_background_tasks(test_db):
    u1_id, _, _, _ = _seed_users_and_news(test_db)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    with patch("app.services.news_service.send_new_news_notification.delay") as mock_delay:
        mock_delay.return_value.id = "mock-task-123"
        resp = client.post(
            "/news",
            json={
                "title": "API Triggered News",
                "content": {"text": "Hello"},
                "author_id": u1_id,
            },
        )
        assert resp.status_code == 201
        created_id = resp.json()["id"]
        mock_delay.assert_called_once_with(created_id)

    with patch("app.controllers.notification_controller.send_weekly_digest.delay") as mock_digest:
        mock_digest.return_value.id = "digest-task-456"
        resp = client.post("/notifications/digest")
        assert resp.status_code == 202
        assert resp.json() == {"task_id": "digest-task-456", "status": "queued"}
