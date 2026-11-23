from datetime import datetime, timedelta, timezone
from secrets import compare_digest
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.tokens import issue_token, read_token, token_hash, unauthorized
from app.config import settings
from app.models import RefreshSession
from app.schemas.auth import TokenPair


def _rotate(session: RefreshSession, now: datetime) -> TokenPair:
    access_expires_at = min(now + timedelta(minutes=settings.access_token_minutes), session.expires_at)
    tokens = TokenPair(
        access_token=issue_token(session.user_id, session.id, "access", now, access_expires_at),
        refresh_token=issue_token(session.user_id, session.id, "refresh", now, session.expires_at),
    )
    session.token_hash = token_hash(tokens.refresh_token)
    return tokens


def start_session(db: Session, user_id: int, user_agent: str | None) -> TokenPair:
    now = datetime.now(timezone.utc)
    session = RefreshSession(
        id=uuid4(),
        user_id=user_id,
        user_agent=user_agent[:1024] if user_agent else None,
        expires_at=now + timedelta(days=settings.refresh_token_days),
    )
    tokens = _rotate(session, now)
    db.add(session)
    db.commit()
    return tokens


def _locked_session(db: Session, refresh_token: str) -> RefreshSession:
    claims = read_token(refresh_token, "refresh")
    session = db.get(RefreshSession, claims.session_id, with_for_update=True)
    if (
        session is None
        or session.user_id != claims.user_id
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(timezone.utc)
        or not compare_digest(session.token_hash, token_hash(refresh_token))
    ):
        raise unauthorized()
    return session


def refresh(db: Session, refresh_token: str) -> TokenPair:
    session = _locked_session(db, refresh_token)
    tokens = _rotate(session, datetime.now(timezone.utc))
    db.commit()
    return tokens


def logout(db: Session, refresh_token: str) -> None:
    session = _locked_session(db, refresh_token)
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()


def list_sessions(db: Session, user_id: int) -> list[RefreshSession]:
    stmt = (
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > datetime.now(timezone.utc),
        )
        .order_by(RefreshSession.created_at.desc(), RefreshSession.id)
    )
    return list(db.scalars(stmt))
