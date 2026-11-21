from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comment import CommentRead
from app.schemas.news import NewsCreate, NewsRead, NewsUpdate
from app.services import comment_service, news_service

router = APIRouter(prefix="/news", tags=["News"])


@router.post("", response_model=NewsRead, status_code=status.HTTP_201_CREATED)
def create_news(payload: NewsCreate, db: Session = Depends(get_db)) -> NewsRead:
    return news_service.create_news(db, payload)


@router.get("", response_model=list[NewsRead])
def list_news(
    author_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> list[NewsRead]:
    return news_service.list_news(db, author_id=author_id)


@router.get("/{news_id}", response_model=NewsRead)
def get_news(news_id: int, db: Session = Depends(get_db)) -> NewsRead:
    return news_service.get_news(db, news_id)


@router.get("/{news_id}/comments", response_model=list[CommentRead])
def list_news_comments(news_id: int, db: Session = Depends(get_db)) -> list[CommentRead]:
    news_service.get_news(db, news_id)
    return comment_service.list_comments(db, news_id=news_id)


@router.patch("/{news_id}", response_model=NewsRead)
def update_news(news_id: int, payload: NewsUpdate, db: Session = Depends(get_db)) -> NewsRead:
    return news_service.update_news(db, news_id, payload)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news_id: int, db: Session = Depends(get_db)) -> Response:
    news_service.delete_news(db, news_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
