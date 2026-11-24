from pydantic import PositiveInt, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/news_api"

    redis_url: str = "redis://localhost:6379/0"
    access_token_ttl_seconds: PositiveInt = 900
    refresh_token_ttl_seconds: PositiveInt = 604800

    @model_validator(mode="after")
    def validate_token_lifetimes(self) -> "Settings":
        if self.access_token_ttl_seconds >= self.refresh_token_ttl_seconds:
            raise ValueError("Access token lifetime must be shorter than refresh token lifetime")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
