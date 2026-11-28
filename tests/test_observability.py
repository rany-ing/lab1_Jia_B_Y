import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.observability.logging import configure_structlog


@pytest.fixture()
def obs_env(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "obs_test.db"
    app_log = tmp_path / "app.log"
    metrics_json = tmp_path / "metrics.json"

    monkeypatch.setattr(settings, "app_log_file", str(app_log))
    monkeypatch.setattr(settings, "metrics_json_file", str(metrics_json))

    logger = logging.getLogger("news_api")
    for h in list(logger.handlers):
        h.close()
        logger.removeHandler(h)
    configure_structlog()

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
        yield app_log, metrics_json
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_prometheus_business_metrics_and_json_export(obs_env):
    _, metrics_json = obs_env
    client = TestClient(app)

    user_resp = client.post(
        "/users",
        json={
            "name": "Metrics Author",
            "email": "metrics_author@example.com",
            "is_verified_author": True,
        },
    )
    assert user_resp.status_code == 201
    author_id = user_resp.json()["id"]

    with patch("app.services.news_service.send_new_news_notification.delay") as mock_delay:
        mock_delay.return_value.id = "obs-task-1"
        news_resp = client.post(
            "/news",
            json={
                "title": "Observability Launch",
                "content": {"text": "Prometheus + Grafana + ELK + Hawk"},
                "author_id": author_id,
            },
        )
        assert news_resp.status_code == 201

    prom_resp = client.get("/metrics")
    assert prom_resp.status_code == 200
    assert "news_created_total" in prom_resp.text
    assert "users_registered_total" in prom_resp.text
    assert "news_notifications_sent_total" in prom_resp.text or "http_requests_total" in prom_resp.text

    json_resp = client.get("/metrics/json")
    assert json_resp.status_code == 200
    payload = json_resp.json()
    assert "exported_at" in payload
    metric_names = {m["name"] for m in payload["metrics"]}
    assert "news_created" in metric_names or "news_created_total" in metric_names
    assert "users_registered" in metric_names or "users_registered_total" in metric_names

    assert metrics_json.exists()
    saved = json.loads(metrics_json.read_text(encoding="utf-8"))
    assert "exported_at" in saved
    assert isinstance(saved["metrics"], list)


def test_structlog_json_logs_and_hawk_error_capture(obs_env):
    app_log, _ = obs_env
    client = TestClient(app, raise_server_exceptions=False)

    ok_resp = client.get("/health")
    assert ok_resp.status_code == 200
    assert "X-Request-ID" in ok_resp.headers

    not_found_resp = client.get("/news/999999")
    assert not_found_resp.status_code == 404

    with patch("app.observability.middleware.capture_exception") as mock_capture:
        err_resp = client.get("/debug/error")
        assert err_resp.status_code == 500
        assert err_resp.json()["detail"] == "Internal Server Error"
        mock_capture.assert_called_once()

    lines = [line for line in app_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 3
    parsed = [json.loads(line) for line in lines]

    events = {entry["event"]: entry for entry in parsed}
    assert "http_request" in events
    assert "http_error" in events
    assert "unhandled_exception" in events
    assert events["unhandled_exception"]["error_type"] == "RuntimeError"
    assert events["unhandled_exception"]["path"] == "/debug/error"
