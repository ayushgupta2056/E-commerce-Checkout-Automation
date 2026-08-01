from pathlib import Path

from playwright.sync_api import Page

from utilities.config_reader import SCREENSHOT_DIR


def save_screenshot(page: Page, name: str) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True, timeout=5000)
    return path
