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
    """Wipe and re-init the SQLite DB before every test."""
    from app.db import DB_PATH, init_db
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


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
