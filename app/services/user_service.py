from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.observability.metrics import export_metrics_to_json, users_registered_total, users_total
from app.schemas.user import UserCreate, UserUpdate


def _sync_users_gauge(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(User)) or 0
    users_total.set(count)


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


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
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

    users_registered_total.inc()
    _sync_users_gauge(db)
    export_metrics_to_json()
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
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()
    _sync_users_gauge(db)
    export_metrics_to_json()
