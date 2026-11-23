from fastapi import FastAPI

from app.controllers import comment_router, news_router, user_router
from app.controllers.auth_controller import router as auth_router

app = FastAPI(
    title="News Management API",
    description="CRUD API for Users, News (JSON content), and Comments built with FastAPI, SQLAlchemy, Alembic, and PostgreSQL.",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(news_router)
app.include_router(comment_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
