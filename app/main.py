from fastapi import FastAPI

from app.controllers import comment_router, news_router, notification_router, user_router

app = FastAPI(
    title="News Management API",
    description="CRUD API for Users, News (JSON content), Comments, and Celery/Redis Email Mock Notifications.",
    version="1.1.0",
)

app.include_router(user_router)
app.include_router(news_router)
app.include_router(comment_router)
app.include_router(notification_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
