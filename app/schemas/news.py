from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NewsCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: dict[str, Any] | list[Any]
    author_id: int = Field(..., gt=0)
    cover: str | None = Field(default=None, max_length=500)


class NewsUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: dict[str, Any] | list[Any] | None = None
    cover: str | None = Field(default=None, max_length=500)


class NewsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: dict[str, Any] | list[Any]
    published_at: datetime
    author_id: int
    cover: str | None = None
