import time
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.hawk_setup import capture_exception
from app.observability.logging import get_structlog_logger

logger = get_structlog_logger("news_api.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "unhandled_exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query=str(request.url.query),
                client_ip=request.client.host if request.client else None,
                duration_ms=duration_ms,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            capture_exception(
                exc,
                context={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log_payload = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

        if response.status_code >= 400:
            logger.error("http_error", **log_payload)
        else:
            logger.info("http_request", **log_payload)

        response.headers["X-Request-ID"] = request_id
        return response
