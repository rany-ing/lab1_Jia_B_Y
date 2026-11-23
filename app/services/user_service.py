from fastapi import HTTPException, status
from fastapi_sso.sso.base import OpenID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.github import verified_email
from app.auth.passwords import hasher
from app.models.user import User
from app.schemas.auth import Register
from app.schemas.user import UserCreate, UserUpdate


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)).all())


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found",
        )
    return user


def find_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def _commit_user(db: Session, user: User) -> User:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Email address already in use") from exc
    db.refresh(user)
    return user


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump(exclude={"password"}))
    if isinstance(payload, Register):
        user.password_hash = hasher.hash(payload.password.get_secret_value())
    db.add(user)
    return _commit_user(db, user)


def get_or_create_github_user(db: Session, identity: OpenID) -> User:
    by_github_id = select(User).where(User.github_id == identity.id)
    user = db.scalar(by_github_id)
    if user is not None:
        return user

    email = verified_email(identity)
    user = User(
        github_id=identity.id,
        email=email,
        name=(identity.display_name or "GitHub user")[:120],
        avatar=identity.picture[:500] if identity.picture else None,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # Another callback may have just created this same GitHub account.
        user = db.scalar(by_github_id)
        if user is None:
            raise HTTPException(409, "GitHub email belongs to an existing account") from exc
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    return _commit_user(db, user)


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
