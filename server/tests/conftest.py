"""Pytest fixtures — fresh SQLite DB for every test."""
import os
import sys
from pathlib import Path

# Make sure the app/ package is importable without `python -m`.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Force mock mode so tests don't hit Gemini API.
os.environ["USE_MOCK_GEMINI"] = "true"
os.environ["USE_MOCK_VISION"] = "true"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def fresh_db():
    """Wipe and re-init the SQLite DB before every test.

    On Windows, file unlink can race with the FastAPI test client closing its
    connection — swallow PermissionError and clear the tables instead.
    """
    from app.db import DB_PATH, init_db, get_db
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            # File held by a lingering connection — clear contents instead
            conn = get_db()
            for tbl in ("claim_evidence", "claims", "evaluation_turns",
                        "evaluation_sessions", "ring_clusters",
                        "address_signatures", "orders", "customers"):
                try:
                    conn.execute(f"DELETE FROM {tbl}")
                except Exception:
                    pass
            conn.commit()
            conn.close()
    init_db()
    yield
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except PermissionError:
            pass


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def db():
    from app.db import get_db
    conn = get_db()
    yield conn
    conn.close()
