from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from app.schemas.user import UserCreate


class Register(UserCreate):
    password: SecretStr = Field(min_length=8, max_length=256)


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255)
    password: SecretStr = Field(min_length=1, max_length=256)


class RefreshToken(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: SecretStr = Field(min_length=1, max_length=4096)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class SessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_agent: str | None
    created_at: datetime
    expires_at: datetime
