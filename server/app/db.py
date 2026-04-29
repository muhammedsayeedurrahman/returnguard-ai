import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent
DB_PATH = ROOT / "sec_logistics.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db() -> sqlite3.Connection:
    # check_same_thread=False — fusion runs scorers via asyncio.to_thread which
    # spawns worker threads. SQLite itself is thread-safe; only the Python
    # wrapper enforces thread affinity by default.
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_db()
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    conn.close()
