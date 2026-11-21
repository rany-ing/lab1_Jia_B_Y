from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.schemas.news import NewsCreate, NewsRead, NewsUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "NewsCreate",
    "NewsUpdate",
    "NewsRead",
    "CommentCreate",
    "CommentUpdate",
    "CommentRead",
]
