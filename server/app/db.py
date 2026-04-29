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
    # Idempotent migrations — add new columns if running on an older DB.
    _ensure_column(conn, "claims", "video_path", "TEXT")
    _ensure_column(conn, "claims", "capture_method", "TEXT DEFAULT 'file_upload'")
    _ensure_column(conn, "claims", "fraud_context", "TEXT DEFAULT 'default'")
    conn.commit()
    conn.close()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str,
                   spec: str) -> None:
    """ALTER TABLE … ADD COLUMN if the column doesn't already exist."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    existing = {r["name"] for r in rows}
    if column not in existing:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {spec}")
        except sqlite3.OperationalError:
            pass  # race / older sqlite — schema.sql will handle on fresh DB
