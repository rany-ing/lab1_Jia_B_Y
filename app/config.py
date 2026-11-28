from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/news_api"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    notification_log_file: str = "logs/notifications.log"
    app_log_file: str = "logs/app.log"
    metrics_json_file: str = "logs/metrics.json"
    hawk_token: str | None = None
    notification_idempotency_ttl_seconds: int = 60 * 60 * 24 * 30
    celery_task_always_eager: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
