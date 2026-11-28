from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.user import User


@pytest.fixture()
def db_session_factory(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "app_test.db"
    metrics_json = tmp_path / "metrics.json"
    monkeypatch.setattr(settings, "metrics_json_file", str(metrics_json))

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def db_session(db_session_factory) -> Session:
    db = db_session_factory()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session: Session) -> User:
    """Fixture providing a verified author user for API and E2E tests."""
    user = User(
        name="Test Verified Author",
        email="test_author@example.com",
        is_verified_author=True,
        avatar="https://example.com/avatar.png",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def reader_user(db_session: Session) -> User:
    """Fixture providing a regular unverified reader user."""
    user = User(
        name="Test Reader",
        email="test_reader@example.com",
        is_verified_author=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest_asyncio.fixture()
async def async_client(db_session_factory):
    with patch("app.services.news_service.send_new_news_notification.delay") as mock_delay:
        mock_delay.return_value.id = "test-celery-task-id"
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
