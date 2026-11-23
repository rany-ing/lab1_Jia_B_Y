from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/news_api"

    jwt_secret: SecretStr = SecretStr("")
    access_token_minutes: int = Field(default=15, gt=0)
    refresh_token_days: int = Field(default=30, gt=0)
    github_client_id: str = ""
    github_client_secret: SecretStr = SecretStr("")
    github_callback_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000/auth/github/callback")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
