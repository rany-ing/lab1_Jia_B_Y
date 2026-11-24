import logging
from collections.abc import Callable
from typing import TypeVar

from pydantic import TypeAdapter, ValidationError
from redis import Redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger("uvicorn.error")
redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)

T = TypeVar("T")


def cached(
    scope: str,
    key: str,
    adapter: TypeAdapter[T],
    ttl: int,
    load: Callable[[], T],
) -> T:
    try:
        revision = redis.get(f"news-api:revision:{scope}") or "0"
        cache_key = f"news-api:cache:{scope}:{revision}:{key}"
        value = redis.get(cache_key)
    except RedisError:
        logger.warning("cache=unavailable scope=%s key=%s source=postgres", scope, key)
        return load()

    if value is not None:
        try:
            result = adapter.validate_json(value)
        except ValidationError:
            logger.warning("cache=invalid scope=%s key=%s", scope, key)
        else:
            logger.info("cache=hit scope=%s key=%s source=redis", scope, key)
            return result

    logger.info("cache=miss scope=%s key=%s source=postgres", scope, key)
    result = load()
    try:
        redis.set(cache_key, adapter.dump_json(result), ex=ttl)
    except RedisError:
        logger.warning("cache=write_failed scope=%s key=%s", scope, key)
    return result


def invalidate(scope: str) -> None:
    # An in-flight reader can only fill the revision it read before querying PostgreSQL.
    try:
        redis.incr(f"news-api:revision:{scope}")
    except RedisError:
        logger.warning("cache=invalidation_failed scope=%s", scope)
