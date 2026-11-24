from fastapi import HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cache import cached, invalidate
from app.models.user import User
from app.schemas.user import UserCreate, UserRole, UserUpdate

role_adapter = TypeAdapter(UserRole)


def get_role(db: Session, user_id: int) -> UserRole:
    def load_role() -> UserRole:
        role = db.scalar(select(User.is_verified_author).where(User.id == user_id))
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id={user_id} not found",
            )
        return UserRole(id=user_id, is_verified_author=role)

    return cached("roles", str(user_id), role_adapter, 60, load_role)


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


def create_user(db: Session, payload: UserCreate, *, password_hash: str | None = None) -> User:
    user = User(**payload.model_dump(), password_hash=password_hash)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists",
        ) from exc
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate) -> User:
    user = get_user(db, user_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{payload.email}' already exists",
        ) from exc
    if "is_verified_author" in updates:
        invalidate("roles")
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    invalidate("roles")
    invalidate("news")
