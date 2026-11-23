from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.auth.dependencies import Db, current_user, editable_news, require_publisher
from app.models import News, User
from app.schemas.comment import CommentRead
from app.schemas.news import NewsCreate, NewsRead, NewsUpdate
from app.services import comment_service, news_service

Publisher = Annotated[User, Depends(require_publisher)]
EditableNews = Annotated[News, Depends(editable_news)]

router = APIRouter(prefix="/news", tags=["News"], dependencies=[Depends(current_user)])


@router.post("", response_model=NewsRead, status_code=status.HTTP_201_CREATED)
def create_news(payload: NewsCreate, user: Publisher, db: Db) -> NewsRead:
    return news_service.create_news(db, payload, user.id)


@router.get("", response_model=list[NewsRead])
def list_news(
    db: Db,
    author_id: int | None = Query(default=None, gt=0),
) -> list[NewsRead]:
    return news_service.list_news(db, author_id=author_id)


@router.get("/{news_id}", response_model=NewsRead)
def get_news(news_id: int, db: Db) -> NewsRead:
    return news_service.get_news(db, news_id)


@router.get("/{news_id}/comments", response_model=list[CommentRead])
def list_news_comments(news_id: int, db: Db) -> list[CommentRead]:
    news_service.get_news(db, news_id)
    return comment_service.list_comments(db, news_id=news_id)


@router.patch("/{news_id}", response_model=NewsRead)
def update_news(payload: NewsUpdate, news: EditableNews, db: Db) -> NewsRead:
    return news_service.update_news(db, news, payload)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news: EditableNews, db: Db) -> Response:
    news_service.delete_news(db, news)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
