from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

from utilities.config_reader import DATABASE_PATH, PROJECT_ROOT
from utilities.logger import get_logger


logger = get_logger(__name__)


class DatabaseClient:
    """Small SQLite helper for parameterized validation queries."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        return self.connection

    def execute_select_one(self, query: str, params: tuple = ()) -> dict | None:
        logger.info("Executing database SELECT one")
        connection = self.connection or self.connect()
        row = connection.execute(query, params).fetchone()
        return dict(row) if row else None

    def execute_select_many(self, query: str, params: tuple = ()) -> list[dict]:
        logger.info("Executing database SELECT many")
        connection = self.connection or self.connect()
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None


def reset_test_data() -> None:
    logger.info("Resetting SQLite test data")
    sys.path.insert(0, str(PROJECT_ROOT / "database"))
    from reset_database import reset_database

    reset_database()
