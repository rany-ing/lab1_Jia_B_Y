from pydantic import BaseModel, EmailStr, Field, SecretStr

from app.schemas.user import UserCreate


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=256)

    def user_payload(self) -> UserCreate:
        return UserCreate(name=self.name, email=self.email)


class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(max_length=256)


class RefreshRequest(BaseModel):
    refresh_token: SecretStr = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
