from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=255)
    avatar: str | None = Field(default=None, max_length=500)


class AdminUserCreate(UserCreate):
    is_verified_author: bool = False
    is_admin: bool = False


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = Field(default=None, max_length=255)
    avatar: str | None = Field(default=None, max_length=500)
    is_verified_author: bool | None = None
    is_admin: bool | None = None

    @model_validator(mode="after")
    def reject_null_fields(self) -> "UserUpdate":
        for field in self.model_fields_set - {"avatar"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    registered_at: datetime
    is_verified_author: bool
    is_admin: bool
    avatar: str | None = None
