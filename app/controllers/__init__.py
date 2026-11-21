from app.controllers.comment_controller import router as comment_router
from app.controllers.news_controller import router as news_router
from app.controllers.user_controller import router as user_router

__all__ = ["user_router", "news_router", "comment_router"]
