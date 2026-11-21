from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1)
    news_id: int = Field(..., gt=0)
    author_id: int = Field(..., gt=0)


class CommentUpdate(BaseModel):
    text: str = Field(..., min_length=1)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    news_id: int
    author_id: int
    published_at: datetime
