import socket
import threading
import time
from unittest.mock import patch

import pytest
import uvicorn
from playwright.async_api import async_playwright

from app.main import app

HOST = "localhost"


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


@pytest.fixture()
def live_server_url(db_session_factory, test_user):
    port = _find_free_port()
    config = uvicorn.Config(app, host=HOST, port=port, log_level="warning")
    server = uvicorn.Server(config)

    with patch("app.services.news_service.send_new_news_notification.delay") as mock_delay:
        mock_delay.return_value.id = "e2e-task-id"
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        deadline = time.time() + 10
        while not server.started and time.time() < deadline:
            time.sleep(0.05)

        yield f"http://{HOST}:{port}"

        server.should_exit = True
        thread.join(timeout=5)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_news_crud_e2e_via_ui(live_server_url, test_user):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(f"{live_server_url}/ui", wait_until="networkidle")

        # 1. Create news through UI
        await page.fill("#news-title", "Playwright E2E News")
        await page.fill("#news-content", "Initial E2E body text")
        await page.click("#submit-btn")

        # 2. Read news in list and detail panel
        await page.wait_for_selector(".news-item h3:has-text('Playwright E2E News')")
        await page.click(".news-item button:has-text('Read')")
        assert await page.locator("#detail-title").text_content() == "Playwright E2E News"
        assert await page.locator("#detail-content").text_content() == "Initial E2E body text"

        # 3. Edit news through UI
        await page.click(".news-item button:has-text('Edit')")
        await page.fill("#news-title", "Playwright E2E News Updated")
        await page.fill("#news-content", "Updated E2E body text")
        await page.click("#submit-btn")

        await page.wait_for_selector(".news-item h3:has-text('Playwright E2E News Updated')")
        assert await page.locator("#detail-title").text_content() == "Playwright E2E News Updated"
        assert await page.locator("#detail-content").text_content() == "Updated E2E body text"

        # 4. Delete news through UI
        await page.click(".news-item button:has-text('Delete')")
        await page.wait_for_selector("#news-list:has-text('No news yet.')")
        assert await page.locator(".news-item").count() == 0

        await browser.close()
