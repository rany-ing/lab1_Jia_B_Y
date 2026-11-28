from app.observability.hawk_setup import capture_exception, init_hawk
from app.observability.logging import configure_structlog, get_structlog_logger
from app.observability.metrics import (
    export_metrics_to_json,
    news_created_total,
    news_notifications_failed_total,
    news_notifications_sent_total,
    news_notifications_skipped_total,
    news_total,
    users_registered_total,
    users_total,
)
from app.observability.middleware import RequestLoggingMiddleware

__all__ = [
    "RequestLoggingMiddleware",
    "capture_exception",
    "configure_structlog",
    "export_metrics_to_json",
    "get_structlog_logger",
    "init_hawk",
    "news_created_total",
    "news_notifications_failed_total",
    "news_notifications_sent_total",
    "news_notifications_skipped_total",
    "news_total",
    "users_registered_total",
    "users_total",
]
