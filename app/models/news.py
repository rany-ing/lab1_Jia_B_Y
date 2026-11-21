from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.comment import Comment
    from app.models.user import User


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[dict[str, Any] | list[Any]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    cover: Mapped[str | None] = mapped_column(String(500), nullable=True)

    author: Mapped["User"] = relationship(back_populates="news")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="news",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
