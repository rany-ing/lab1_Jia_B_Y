from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.tokens import read_token, unauthorized
from app.database import get_db
from app.models import Comment, News, RefreshSession, User
from app.services import comment_service, news_service

Db = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Db,
) -> User:
    if credentials is None:
        raise unauthorized()
    claims = read_token(credentials.credentials, "access")
    session = db.get(RefreshSession, claims.session_id)
    if (
        session is None
        or session.user_id != claims.user_id
        or session.revoked_at is not None
        or session.expires_at <= datetime.now(timezone.utc)
    ):
        raise unauthorized()
    user = db.get(User, claims.user_id)
    if user is None:
        raise unauthorized()
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise HTTPException(403, "Administrator access required")
    return user


def require_owner_or_admin(user: User, owner_id: int) -> None:
    if user.id != owner_id and not user.is_admin:
        raise HTTPException(403, "You can only manage your own resources")


def require_publisher(user: CurrentUser) -> User:
    if not (user.is_verified_author or user.is_admin):
        raise HTTPException(403, "Only verified authors and administrators can publish news")
    return user


def editable_news(news_id: int, user: CurrentUser, db: Db) -> News:
    news = news_service.get_news(db, news_id)
    require_owner_or_admin(user, news.author_id)
    return news


def editable_comment(comment_id: int, user: CurrentUser, db: Db) -> Comment:
    comment = comment_service.get_comment(db, comment_id)
    require_owner_or_admin(user, comment.author_id)
    return comment
