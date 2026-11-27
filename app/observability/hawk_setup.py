from typing import Any

from fastapi import FastAPI
from hawk_python_sdk.modules.fastapi import HawkFastapi

from app.config import settings
from app.observability.logging import get_structlog_logger

logger = get_structlog_logger("news_api.hawk")

_hawk_client: HawkFastapi | None = None


def init_hawk(app: FastAPI) -> HawkFastapi | None:
    global _hawk_client
    if not settings.hawk_token:
        logger.info("hawk_disabled", reason="HAWK_TOKEN is not set")
        return None

    _hawk_client = HawkFastapi(
        {
            "app_instance": app,
            "token": settings.hawk_token,
        }
    )
    logger.info("hawk_initialized")
    return _hawk_client


def capture_exception(exc: Exception, context: dict[str, Any] | None = None) -> bool:
    if _hawk_client is None:
        return False
    try:
        _hawk_client.send(exc, context=context or {})
        return True
    except Exception as send_exc:
        logger.warning("hawk_send_failed", error=str(send_exc))
        return False
