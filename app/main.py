from typing import Any

from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.controllers import (
    comment_router,
    news_router,
    notification_router,
    ui_router,
    user_router,
)
from app.database import get_db
from app.models.news import News
from app.models.user import User
from app.observability import (
    RequestLoggingMiddleware,
    configure_structlog,
    export_metrics_to_json,
    init_hawk,
    news_total,
    users_total,
)

configure_structlog()

app = FastAPI(
    title="News Management API",
    description="CRUD API for Users, News, Comments, Celery Notifications, Prometheus/Grafana Metrics, ELK JSON Logging, and Hawk Error Tracking.",
    version="1.2.0",
)

init_hawk(app)
app.add_middleware(RequestLoggingMiddleware)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)

app.include_router(user_router)
app.include_router(news_router)
app.include_router(comment_router)
app.include_router(notification_router)
app.include_router(ui_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics/json", tags=["Observability"])
def metrics_json(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        news_count = db.scalar(select(func.count()).select_from(News)) or 0
        users_count = db.scalar(select(func.count()).select_from(User)) or 0
        news_total.set(news_count)
        users_total.set(users_count)
    except Exception:
        pass
    return export_metrics_to_json()


@app.get("/debug/error", tags=["Observability"])
def trigger_test_error() -> None:
    raise RuntimeError("Intentional test error for Hawk & structured JSON logging")
