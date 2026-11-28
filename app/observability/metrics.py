import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prometheus_client import REGISTRY, Counter, Gauge

from app.config import settings

news_created_total = Counter(
    "news_created_total",
    "Total number of created news items",
)

users_registered_total = Counter(
    "users_registered_total",
    "Total number of registered users",
)

news_total = Gauge(
    "news_total",
    "Current number of news items in database",
)

users_total = Gauge(
    "users_total",
    "Current number of users in database",
)

news_notifications_sent_total = Counter(
    "news_notifications_sent_total",
    "Total number of mock email notifications sent",
    ["notification_type"],
)

news_notifications_skipped_total = Counter(
    "news_notifications_skipped_total",
    "Total number of idempotent skipped notifications",
    ["notification_type"],
)

news_notifications_failed_total = Counter(
    "news_notifications_failed_total",
    "Total number of failed notification tasks",
    ["notification_type"],
)


def collect_metrics_snapshot() -> dict[str, Any]:
    families: list[dict[str, Any]] = []
    for metric in REGISTRY.collect():
        samples = [
            {
                "name": sample.name,
                "labels": dict(sample.labels),
                "value": sample.value,
            }
            for sample in metric.samples
        ]
        families.append(
            {
                "name": metric.name,
                "type": metric.type,
                "documentation": metric.documentation,
                "samples": samples,
            }
        )

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "metrics": families,
    }


def export_metrics_to_json(filepath: str | Path | None = None) -> dict[str, Any]:
    target = Path(filepath or settings.metrics_json_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot = collect_metrics_snapshot()
    tmp_path = target.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(target)
    return snapshot
