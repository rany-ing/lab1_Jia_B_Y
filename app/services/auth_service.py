import hashlib
import hmac
import secrets
import time
from uuid import uuid4

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
from redis.client import Pipeline
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import logger, redis
from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair
from app.schemas.user import UserRole
from app.services.user_service import create_user, get_role

PASSWORD_ITERATIONS = 600_000


def password_digest(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)


class SessionRecord(BaseModel):
    user_id: int
    access_digest: str
    refresh_digest: str
    access_expires_at: int
    refresh_expires_at: int


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def session_store_unavailable() -> HTTPException:
    logger.warning("cache=unavailable scope=sessions")
    return HTTPException(status_code=503, detail="Session store unavailable")


def register(db: Session, payload: RegisterRequest) -> User:
    salt = secrets.token_bytes(16)
    digest = password_digest(payload.password.get_secret_value(), salt)
    return create_user(db, payload.user_payload(), password_hash=f"{salt.hex()}:{digest.hex()}")


def session_key(session_id: str) -> str:
    return f"news-api:session:{session_id}"


def token_digest(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def split_token(token: str) -> tuple[str, str]:
    session_id, separator, secret = token.partition(".")
    if not separator or len(session_id) != 32 or len(secret) != 43 or not token.isascii():
        raise invalid_credentials()
    return session_id, token_digest(secret)


def issue_tokens(
    user_id: int, session_id: str, now: int, refresh_expires_at: int
) -> tuple[SessionRecord, TokenPair]:
    access_secret = secrets.token_urlsafe(32)
    refresh_secret = secrets.token_urlsafe(32)
    expires_in = min(settings.access_token_ttl_seconds, refresh_expires_at - now)
    record = SessionRecord(
        user_id=user_id,
        access_digest=token_digest(access_secret),
        refresh_digest=token_digest(refresh_secret),
        access_expires_at=now + expires_in,
        refresh_expires_at=refresh_expires_at,
    )
    tokens = TokenPair(
        access_token=f"{session_id}.{access_secret}",
        refresh_token=f"{session_id}.{refresh_secret}",
        expires_in=expires_in,
    )
    return record, tokens


def login(db: Session, payload: LoginRequest) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email))
    stored = user.password_hash if user else None
    salt, expected = stored.split(":") if stored else ("00" * 16, "00" * 32)
    actual = password_digest(payload.password.get_secret_value(), bytes.fromhex(salt))
    if not hmac.compare_digest(actual, bytes.fromhex(expected)) or user is None or stored is None:
        raise invalid_credentials()

    session_id = uuid4().hex
    now = int(time.time())
    ttl = settings.refresh_token_ttl_seconds
    record, tokens = issue_tokens(user.id, session_id, now, now + ttl)
    try:
        redis.set(session_key(session_id), record.model_dump_json(), ex=ttl)
    except RedisError as exc:
        raise session_store_unavailable() from exc
    logger.info("cache=write scope=sessions source=redis")
    return tokens


def read_session(value: str | None) -> SessionRecord:
    if value is None:
        logger.info("cache=miss scope=sessions source=redis")
        raise invalid_credentials()
    try:
        record = SessionRecord.model_validate_json(value)
    except ValidationError as exc:
        logger.warning("cache=invalid scope=sessions")
        raise invalid_credentials() from exc
    logger.info("cache=hit scope=sessions source=redis")
    return record


def session_user(db: Session, user_id: int) -> UserRole:
    try:
        return get_role(db, user_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            raise invalid_credentials() from exc
        raise


def authenticate(db: Session, token: str) -> UserRole:
    session_id, digest = split_token(token)
    try:
        record = read_session(redis.get(session_key(session_id)))
    except RedisError as exc:
        raise session_store_unavailable() from exc
    if record.access_expires_at <= time.time() or not hmac.compare_digest(record.access_digest, digest):
        raise invalid_credentials()
    return session_user(db, record.user_id)


def refresh(db: Session, token: str) -> TokenPair:
    session_id, digest = split_token(token)
    key = session_key(session_id)
    tokens: TokenPair

    def rotate(pipe: Pipeline) -> None:
        nonlocal tokens
        record = read_session(pipe.get(key))
        now = int(time.time())
        if record.refresh_expires_at <= now or not hmac.compare_digest(record.refresh_digest, digest):
            raise invalid_credentials()
        session_user(db, record.user_id)
        replacement, tokens = issue_tokens(
            record.user_id, session_id, now, record.refresh_expires_at
        )
        pipe.multi()
        pipe.set(key, replacement.model_dump_json(), keepttl=True)

    try:
        redis.transaction(rotate, key)
    except RedisError as exc:
        raise session_store_unavailable() from exc
    return tokens
