from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.auth.dependencies import CurrentUser, Db, current_user, editable_comment
from app.models import Comment
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services import comment_service

EditableComment = Annotated[Comment, Depends(editable_comment)]

router = APIRouter(prefix="/comments", tags=["Comments"], dependencies=[Depends(current_user)])


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentCreate, user: CurrentUser, db: Db) -> CommentRead:
    return comment_service.create_comment(db, payload, user.id)


@router.get("", response_model=list[CommentRead])
def list_comments(
    db: Db,
    news_id: int | None = Query(default=None, gt=0),
    author_id: int | None = Query(default=None, gt=0),
) -> list[CommentRead]:
    return comment_service.list_comments(db, news_id=news_id, author_id=author_id)


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment(comment_id: int, db: Db) -> CommentRead:
    return comment_service.get_comment(db, comment_id)


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    payload: CommentUpdate,
    comment: EditableComment,
    db: Db,
) -> CommentRead:
    return comment_service.update_comment(db, comment, payload)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment: EditableComment, db: Db) -> Response:
    comment_service.delete_comment(db, comment)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
