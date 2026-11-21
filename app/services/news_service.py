from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import News
from app.models.user import User
from app.schemas.news import NewsCreate, NewsUpdate


def list_news(db: Session, author_id: int | None = None) -> list[News]:
    stmt = select(News).order_by(News.id)
    if author_id is not None:
        stmt = stmt.where(News.author_id == author_id)
    return list(db.scalars(stmt).all())


def get_news(db: Session, news_id: int) -> News:
    news = db.get(News, news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News with id={news_id} not found",
        )
    return news


def create_news(db: Session, payload: NewsCreate) -> News:
    author = db.get(User, payload.author_id)
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Author with id={payload.author_id} not found",
        )
    if not author.is_verified_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified authors can publish news",
        )

    news = News(**payload.model_dump())
    db.add(news)
    db.commit()
    db.refresh(news)
    return news


def update_news(db: Session, news_id: int, payload: NewsUpdate) -> News:
    news = get_news(db, news_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(news, field, value)
    db.commit()
    db.refresh(news)
    return news


def delete_news(db: Session, news_id: int) -> None:
    news = get_news(db, news_id)
    db.delete(news)
    db.commit()
