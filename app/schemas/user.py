from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    is_verified_author: bool = False
    avatar: str | None = Field(default=None, max_length=500)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    is_verified_author: bool | None = None
    avatar: str | None = Field(default=None, max_length=500)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    registered_at: datetime
    is_verified_author: bool
    avatar: str | None = None
