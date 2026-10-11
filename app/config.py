import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "ecommerce.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "local-qa-demo-secret")
# Public demo deployment only: shows a banner and enables POST /demo/reset.
DEMO_MODE = os.environ.get("DEMO_MODE") == "1"
TAX_RATE = 0.08
DISCOUNT_CODE = "SAVE10"
DISCOUNT_RATE = 0.10
