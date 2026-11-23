from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NewsCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    content: dict[str, Any] | list[Any]
    cover: str | None = Field(default=None, max_length=500)


class NewsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: dict[str, Any] | list[Any] | None = None
    cover: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def reject_null_title_or_content(self) -> "NewsUpdate":
        for field in self.model_fields_set & {"title", "content"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class NewsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: dict[str, Any] | list[Any]
    published_at: datetime
    author_id: int
    cover: str | None = None
