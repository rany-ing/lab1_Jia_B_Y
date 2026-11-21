from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services import comment_service

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
def create_comment(payload: CommentCreate, db: Session = Depends(get_db)) -> CommentRead:
    return comment_service.create_comment(db, payload)


@router.get("", response_model=list[CommentRead])
def list_comments(
    news_id: int | None = Query(default=None, gt=0),
    author_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> list[CommentRead]:
    return comment_service.list_comments(db, news_id=news_id, author_id=author_id)


@router.get("/{comment_id}", response_model=CommentRead)
def get_comment(comment_id: int, db: Session = Depends(get_db)) -> CommentRead:
    return comment_service.get_comment(db, comment_id)


@router.patch("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
) -> CommentRead:
    return comment_service.update_comment(db, comment_id, payload)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db)) -> Response:
    comment_service.delete_comment(db, comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
