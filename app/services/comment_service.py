from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.news import News
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate


def list_comments(
    db: Session,
    news_id: int | None = None,
    author_id: int | None = None,
) -> list[Comment]:
    stmt = select(Comment).order_by(Comment.id)
    if news_id is not None:
        stmt = stmt.where(Comment.news_id == news_id)
    if author_id is not None:
        stmt = stmt.where(Comment.author_id == author_id)
    return list(db.scalars(stmt).all())


def get_comment(db: Session, comment_id: int) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id={comment_id} not found",
        )
    return comment


def create_comment(db: Session, payload: CommentCreate) -> Comment:
    if db.get(News, payload.news_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News with id={payload.news_id} not found",
        )
    if db.get(User, payload.author_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={payload.author_id} not found",
        )

    comment = Comment(**payload.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment_id: int, payload: CommentUpdate) -> Comment:
    comment = get_comment(db, comment_id)
    comment.text = payload.text
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment_id: int) -> None:
    comment = get_comment(db, comment_id)
    db.delete(comment)
    db.commit()
