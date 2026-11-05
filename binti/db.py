"""SQLite connection and lazy seeding.

Local: data/binti.db, persistent.
Vercel: the deploy filesystem is read-only, so the database is seeded into /tmp on cold start.
Writes (chat history, memory, approvals) last while that instance stays warm, then reset to the seed.
"""
import os
import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_lock = threading.Lock()
_conn = None


def db_path() -> str:
    if os.environ.get("BINTI_DB"):
        return os.environ["BINTI_DB"]
    if os.environ.get("VERCEL"):
        return "/tmp/binti.db"
    return str(ROOT / "data" / "binti.db")


def connect() -> sqlite3.Connection:
    """One shared connection per process, seeded on first use."""
    global _conn
    with _lock:
        if _conn is None:
            path = db_path()
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            if not _is_seeded(conn):
                from . import seed
                seed.seed(conn)
            _conn = conn
        return _conn


def reset_for_tests(path=":memory:"):
    """Point the module at a fresh database (used by tests)."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
        _conn = None
    os.environ["BINTI_DB"] = path
    return connect()


def _is_seeded(conn) -> bool:
    try:
        return conn.execute("SELECT 1 FROM meta WHERE k='seeded_on'").fetchone() is not None
    except sqlite3.OperationalError:
        return False


def rows(sql, args=()):
    return [dict(r) for r in connect().execute(sql, args).fetchall()]


def row(sql, args=()):
    r = connect().execute(sql, args).fetchone()
    return dict(r) if r else None


def execute(sql, args=()):
    conn = connect()
    with _lock:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid
