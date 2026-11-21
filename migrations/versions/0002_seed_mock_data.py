"""Seed mock users, news, and comments data.

Revision ID: 0002_seed_mock_data
Revises: 0001_create_initial_tables
Create Date: 2026-11-21 13:31:00
"""
from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision: str = "0002_seed_mock_data"
down_revision: str | Sequence[str] | None = "0001_create_initial_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("email", sa.String()),
        sa.column("registered_at", sa.DateTime(timezone=True)),
        sa.column("is_verified_author", sa.Boolean()),
        sa.column("avatar", sa.String()),
    )

    news_table = sa.table(
        "news",
        sa.column("id", sa.Integer()),
        sa.column("title", sa.String()),
        sa.column("content", sa.JSON()),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("author_id", sa.Integer()),
        sa.column("cover", sa.String()),
    )

    comments_table = sa.table(
        "comments",
        sa.column("id", sa.Integer()),
        sa.column("text", sa.Text()),
        sa.column("news_id", sa.Integer()),
        sa.column("author_id", sa.Integer()),
        sa.column("published_at", sa.DateTime(timezone=True)),
    )

    now = datetime(2026, 11, 21, 10, 0, 0, tzinfo=timezone.utc)

    op.bulk_insert(
        users_table,
        [
            {
                "id": 1,
                "name": "Алиса Смирнова",
                "email": "alice.author@example.com",
                "registered_at": now,
                "is_verified_author": True,
                "avatar": "https://example.com/avatars/alice.png",
            },
            {
                "id": 2,
                "name": "Борис Петров",
                "email": "boris.author@example.com",
                "registered_at": now,
                "is_verified_author": True,
                "avatar": "https://example.com/avatars/boris.png",
            },
            {
                "id": 3,
                "name": "Виктор Иванов",
                "email": "viktor.reader@example.com",
                "registered_at": now,
                "is_verified_author": False,
                "avatar": "https://example.com/avatars/viktor.png",
            },
        ],
    )

    op.bulk_insert(
        news_table,
        [
            {
                "id": 1,
                "title": "Запуск новостного API на FastAPI",
                "content": {
                    "summary": "Первый выпуск сервиса управления новостями и комментариями.",
                    "blocks": [
                        {"type": "paragraph", "text": "Сервис построен на FastAPI, SQLAlchemy и Alembic."},
                        {"type": "paragraph", "text": "Поддерживается хранение контента в формате JSON."},
                    ],
                    "tags": ["fastapi", "postgresql", "release"],
                },
                "published_at": now,
                "author_id": 1,
                "cover": "https://example.com/covers/news-1.jpg",
            },
            {
                "id": 2,
                "title": "Миграции базы данных с Alembic",
                "content": {
                    "summary": "Почему версионирование схемы БД важно для командной разработки.",
                    "blocks": [
                        {"type": "paragraph", "text": "Первая миграция создаёт таблицы и связи."},
                        {"type": "paragraph", "text": "Вторая миграция наполняет БД тестовыми данными."},
                    ],
                    "tags": ["alembic", "migrations"],
                },
                "published_at": now,
                "author_id": 2,
                "cover": "https://example.com/covers/news-2.jpg",
            },
        ],
    )

    op.bulk_insert(
        comments_table,
        [
            {
                "id": 1,
                "text": "Отличный старт! Удобная структура API.",
                "news_id": 1,
                "author_id": 3,
                "published_at": now,
            },
            {
                "id": 2,
                "text": "Спасибо за обратную связь!",
                "news_id": 1,
                "author_id": 1,
                "published_at": now,
            },
            {
                "id": 3,
                "text": "Полезный разбор миграций.",
                "news_id": 2,
                "author_id": 3,
                "published_at": now,
            },
        ],
    )

    # Synchronize PostgreSQL sequences after inserting explicit primary keys
    for table in ("users", "news", "comments"):
        op.execute(
            sa.text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
            )
        )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM comments WHERE id IN (1, 2, 3)"))
    op.execute(sa.text("DELETE FROM news WHERE id IN (1, 2)"))
    op.execute(sa.text("DELETE FROM users WHERE id IN (1, 2, 3)"))
