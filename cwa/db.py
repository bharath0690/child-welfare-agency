"""SQLite connection and lazy seeding.

Local: data/cwa.db, persistent.
Vercel: the deploy filesystem is read-only, so the database is seeded into /tmp on cold start.
Writes (chat history, memory, approvals) last while that instance stays warm, then reset to the seed.
"""
import os
import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_seed_lock = threading.Lock()
_local = threading.local()   # one connection per thread: sqlite3 connections must not be shared across threads
_shared = None               # used only for ":memory:" (tests), which is single-threaded
_generation = 0              # bumped by reset_for_tests so threads drop stale connections


def db_path() -> str:
    if os.environ.get("CWA_DB"):
        return os.environ["CWA_DB"]
    if os.environ.get("VERCEL"):
        return "/tmp/cwa.db"
    return str(ROOT / "data" / "cwa.db")


def _open(path):
    conn = sqlite3.connect(path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


def connect() -> sqlite3.Connection:
    """Return this thread's connection, seeding the database once per file."""
    global _shared
    path = db_path()
    if path == ":memory:":
        with _seed_lock:
            if _shared is None:
                _shared = _open(path)
                if not _is_seeded(_shared):
                    from . import seed
                    seed.seed(_shared)
        return _shared
    conn = getattr(_local, "conn", None)
    if conn is not None and getattr(_local, "gen", None) == (_generation, path):
        return conn
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with _seed_lock:  # only one thread seeds; the others wait and then see a seeded file
        conn = _open(path)
        if not _is_seeded(conn):
            conn.execute("PRAGMA journal_mode = WAL")
            from . import seed
            seed.seed(conn)
    _local.conn, _local.gen = conn, (_generation, path)
    return conn


def reset_for_tests(path=":memory:"):
    """Point the module at a fresh database (used by tests)."""
    global _shared, _generation
    with _seed_lock:
        if _shared is not None:
            _shared.close()
        _shared = None
        _generation += 1
    os.environ["CWA_DB"] = path
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
    cur = conn.execute(sql, args)
    conn.commit()
    return cur.lastrowid
