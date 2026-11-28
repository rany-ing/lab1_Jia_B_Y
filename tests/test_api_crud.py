from unittest.mock import MagicMock, patch

import pytest

from app.observability import hawk_setup


@pytest.mark.asyncio
async def test_health_and_ui_routes(async_client):
    health = await async_client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    ui = await async_client.get("/ui")
    assert ui.status_code == 200
    assert "News Management UI" in ui.text


@pytest.mark.asyncio
async def test_users_crud_and_conflict(async_client, test_user):
    # List & Get existing fixture user
    list_resp = await async_client.get("/users")
    assert list_resp.status_code == 200
    assert any(u["id"] == test_user.id for u in list_resp.json())

    get_resp = await async_client.get(f"/users/{test_user.id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == test_user.email

    missing = await async_client.get("/users/999999")
    assert missing.status_code == 404

    # Create new user
    create_resp = await async_client.post(
        "/users",
        json={
            "name": "New User",
            "email": "new_user@example.com",
            "is_verified_author": False,
        },
    )
    assert create_resp.status_code == 201
    new_user_id = create_resp.json()["id"]

    # Duplicate email returns 409
    dup_resp = await async_client.post(
        "/users",
        json={
            "name": "Duplicate",
            "email": "new_user@example.com",
            "is_verified_author": False,
        },
    )
    assert dup_resp.status_code == 409

    # Update user & conflict on update
    patch_resp = await async_client.patch(
        f"/users/{new_user_id}",
        json={"name": "Updated User", "is_verified_author": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated User"
    assert patch_resp.json()["is_verified_author"] is True

    conflict_patch = await async_client.patch(
        f"/users/{new_user_id}",
        json={"email": test_user.email},
    )
    assert conflict_patch.status_code == 409

    # Delete user
    del_resp = await async_client.delete(f"/users/{new_user_id}")
    assert del_resp.status_code == 204
    assert (await async_client.get(f"/users/{new_user_id}")).status_code == 404


@pytest.mark.asyncio
async def test_news_crud_permissions_and_cascade(async_client, test_user, reader_user):
    # Unverified reader cannot publish news (403)
    forbidden = await async_client.post(
        "/news",
        json={
            "title": "Forbidden News",
            "content": {"text": "Not allowed"},
            "author_id": reader_user.id,
        },
    )
    assert forbidden.status_code == 403

    # Non-existent author returns 404
    missing_author = await async_client.post(
        "/news",
        json={
            "title": "Ghost News",
            "content": {"text": "No author"},
            "author_id": 999999,
        },
    )
    assert missing_author.status_code == 404

    # Verified test_user creates news
    create_resp = await async_client.post(
        "/news",
        json={
            "title": "Async Test News",
            "content": {"text": "Initial content"},
            "author_id": test_user.id,
            "cover": "https://example.com/cover.png",
        },
    )
    assert create_resp.status_code == 201
    news_id = create_resp.json()["id"]

    # Read list & filter by author_id & read single
    all_news = await async_client.get("/news")
    assert all_news.status_code == 200
    assert len(all_news.json()) == 1

    filtered = await async_client.get(f"/news?author_id={test_user.id}")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    single = await async_client.get(f"/news/{news_id}")
    assert single.status_code == 200
    assert single.json()["title"] == "Async Test News"

    # Update news
    updated = await async_client.patch(
        f"/news/{news_id}",
        json={"title": "Edited Async News", "content": {"text": "Updated content"}},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Edited Async News"

    # Add comment then verify cascade delete when news is deleted
    comment_resp = await async_client.post(
        "/comments",
        json={"text": "Nice article!", "news_id": news_id, "author_id": reader_user.id},
    )
    assert comment_resp.status_code == 201

    del_resp = await async_client.delete(f"/news/{news_id}")
    assert del_resp.status_code == 204

    comments_after = await async_client.get(f"/comments?news_id={news_id}")
    assert comments_after.status_code == 200
    assert comments_after.json() == []


@pytest.mark.asyncio
async def test_comments_crud_and_errors(async_client, test_user, reader_user):
    news_resp = await async_client.post(
        "/news",
        json={
            "title": "News for Comments",
            "content": {"text": "Discussion"},
            "author_id": test_user.id,
        },
    )
    news_id = news_resp.json()["id"]

    # Missing news or author returns 404
    assert (
        await async_client.post(
            "/comments",
            json={"text": "Oops", "news_id": 999999, "author_id": reader_user.id},
        )
    ).status_code == 404
    assert (
        await async_client.post(
            "/comments",
            json={"text": "Oops", "news_id": news_id, "author_id": 999999},
        )
    ).status_code == 404

    # Create, list, get, update, delete comment
    created = await async_client.post(
        "/comments",
        json={"text": "First comment", "news_id": news_id, "author_id": reader_user.id},
    )
    assert created.status_code == 201
    comment_id = created.json()["id"]

    news_comments = await async_client.get(f"/news/{news_id}/comments")
    assert news_comments.status_code == 200
    assert len(news_comments.json()) == 1

    by_author = await async_client.get(f"/comments?author_id={reader_user.id}")
    assert by_author.status_code == 200
    assert len(by_author.json()) == 1

    single = await async_client.get(f"/comments/{comment_id}")
    assert single.status_code == 200
    assert single.json()["text"] == "First comment"

    assert (await async_client.get("/comments/999999")).status_code == 404

    edited = await async_client.patch(
        f"/comments/{comment_id}",
        json={"text": "Edited comment"},
    )
    assert edited.status_code == 200
    assert edited.json()["text"] == "Edited comment"

    deleted = await async_client.delete(f"/comments/{comment_id}")
    assert deleted.status_code == 204
    assert (await async_client.get(f"/comments/{comment_id}")).status_code == 404


@pytest.mark.asyncio
async def test_notification_task_status_and_hawk_helpers(async_client):
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_result.ready.return_value = True
    mock_result.result = {"sent": 2}

    with patch("app.controllers.notification_controller.AsyncResult", return_value=mock_result):
        resp = await async_client.get("/notifications/tasks/demo-task-1")
        assert resp.status_code == 200
        assert resp.json() == {"task_id": "demo-task-1", "status": "SUCCESS", "result": {"sent": 2}}

    # Verify hawk capture_exception helper when client is configured vs disabled
    original_client = hawk_setup._hawk_client
    try:
        hawk_setup._hawk_client = None
        assert hawk_setup.capture_exception(RuntimeError("noop")) is False

        fake_hawk = MagicMock()
        hawk_setup._hawk_client = fake_hawk
        assert hawk_setup.capture_exception(RuntimeError("boom"), context={"k": "v"}) is True
        fake_hawk.send.assert_called_once()
    finally:
        hawk_setup._hawk_client = original_client
