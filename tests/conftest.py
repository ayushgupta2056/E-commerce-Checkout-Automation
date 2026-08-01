from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import expect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utilities.api_client import ApiClient
from utilities.config_reader import BASE_URL, SCREENSHOT_DIR
from utilities.database_client import DatabaseClient, reset_test_data
from utilities.logger import get_logger
from utilities.screenshots import save_screenshot


logger = get_logger(__name__)


@pytest.fixture(autouse=True)
def app_server():
    reset_test_data()
    process = subprocess.Popen(
        [sys.executable, "app/app.py"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(40):
        try:
            if requests.get(f"{BASE_URL}/login", timeout=1).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.25)
    else:
        process.terminate()
        raise RuntimeError("FastAPI application did not start on http://127.0.0.1:5000")
    yield
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def api_client() -> ApiClient:
    client = ApiClient()
    client.login()
    return client


@pytest.fixture
def db_client() -> DatabaseClient:
    client = DatabaseClient()
    yield client
    client.close()


@pytest.fixture
def authenticated_page(page, base_url):
    from pages.login_page import LoginPage
    from tests.test_data.test_data import VALID_USER

    login_page = LoginPage(page, base_url)
    login_page.open()
    login_page.login(VALID_USER["email"], VALID_USER["password"])
    page.wait_for_url("**/products", timeout=15000)
    expect(page.get_by_test_id("search-input")).to_be_visible(timeout=15000)
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and "page" in item.funcargs:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = item.name.replace("/", "_").replace("\\", "_")
        try:
            path = save_screenshot(item.funcargs["page"], safe_name)
            logger.info("Failure screenshot saved to %s", path)
        except Exception as exc:
            logger.info("Could not capture screenshot: %s", exc)
