import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_BASE_URL = "http://127.0.0.1:5000"
# Set TARGET_BASE_URL to run the UI and API tests against a deployed demo instead
# of the local app that conftest.py starts. Database tests are skipped then.
BASE_URL = os.environ.get("TARGET_BASE_URL", LOCAL_BASE_URL).rstrip("/")
IS_REMOTE_TARGET = BASE_URL != LOCAL_BASE_URL
DATABASE_PATH = PROJECT_ROOT / "database" / "ecommerce.db"
SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "screenshots"

VALID_USER = {
    "email": "testuser@example.com",
    "password": "Test@123",
}

INVALID_USER = {
    "email": "invalid@example.com",
    "password": "WrongPassword",
}

VALID_PAYMENT = {
    "cardholder_name": "Test User",
    "card_number": "4111111111111111",
    "expiration_date": "12/30",
    "cvv": "123",
}

DECLINED_PAYMENT = {
    "cardholder_name": "Test User",
    "card_number": "4000000000000002",
    "expiration_date": "12/30",
    "cvv": "123",
}
