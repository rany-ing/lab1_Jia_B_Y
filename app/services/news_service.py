from fastapi import HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache import cached, invalidate
from app.models.news import News
from app.schemas.news import NewsCreate, NewsRead, NewsUpdate
from app.services.user_service import get_role

NEWS_TTL_SECONDS = 300
news_adapter = TypeAdapter(NewsRead)
news_list_adapter = TypeAdapter(list[NewsRead])


def list_news(db: Session, author_id: int | None = None) -> list[NewsRead]:
    def load_news() -> list[NewsRead]:
        stmt = select(News).order_by(News.id)
        if author_id is not None:
            stmt = stmt.where(News.author_id == author_id)
        return [NewsRead.model_validate(news) for news in db.scalars(stmt)]

    key = "list" if author_id is None else f"list:author:{author_id}"
    return cached("news", key, news_list_adapter, NEWS_TTL_SECONDS, load_news)


def get_cached_news(db: Session, news_id: int) -> NewsRead:
    return cached(
        "news",
        f"item:{news_id}",
        news_adapter,
        NEWS_TTL_SECONDS,
        lambda: NewsRead.model_validate(get_news(db, news_id)),
    )


def get_news(db: Session, news_id: int) -> News:
    news = db.get(News, news_id)
    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News with id={news_id} not found",
        )
    return news


def create_news(db: Session, payload: NewsCreate) -> News:
    author = get_role(db, payload.author_id)
    if not author.is_verified_author:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified authors can publish news",
        )

    news = News(**payload.model_dump())
    db.add(news)
    db.commit()
    invalidate("news")
    db.refresh(news)
    return news


def update_news(db: Session, news_id: int, payload: NewsUpdate) -> News:
    news = get_news(db, news_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(news, field, value)
    db.commit()
    invalidate("news")
    db.refresh(news)
    return news


def delete_news(db: Session, news_id: int) -> None:
    news = get_news(db, news_id)
    db.delete(news)
    db.commit()
    invalidate("news")
