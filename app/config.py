from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE_PATH = BASE_DIR / "database" / "ecommerce.db"
SECRET_KEY = "local-qa-demo-secret"
TAX_RATE = 0.08
DISCOUNT_CODE = "SAVE10"
DISCOUNT_RATE = 0.10
