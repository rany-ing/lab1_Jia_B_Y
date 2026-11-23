from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.dependencies import CurrentUser, Db, current_user, require_admin, require_owner_or_admin
from app.schemas.user import AdminUserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(current_user)])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user(payload: AdminUserCreate, db: Db) -> UserRead:
    return user_service.create_user(db, payload)


@router.get("", response_model=list[UserRead])
def list_users(db: Db) -> list[UserRead]:
    return user_service.list_users(db)


@router.get("/me", response_model=UserRead)
def get_me(user: CurrentUser) -> UserRead:
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Db) -> UserRead:
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, user: CurrentUser, db: Db) -> UserRead:
    require_owner_or_admin(user, user_id)
    if not user.is_admin and payload.model_fields_set & {"is_admin", "is_verified_author"}:
        raise HTTPException(403, "Only administrators can change roles")
    target = user_service.get_user(db, user_id)
    return user_service.update_user(db, target, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, user: CurrentUser, db: Db) -> Response:
    require_owner_or_admin(user, user_id)
    target = user_service.get_user(db, user_id)
    user_service.delete_user(db, target)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
