import logging
from pathlib import Path

import structlog

from app.config import settings


def configure_structlog() -> None:
    log_path = Path(settings.app_log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("news_api")
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        root_logger.propagate = False

        formatter = logging.Formatter("%(message)s")

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_structlog_logger(name: str = "news_api") -> structlog.stdlib.BoundLogger:
    configure_structlog()
    return structlog.get_logger(name)
