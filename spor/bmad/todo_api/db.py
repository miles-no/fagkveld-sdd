import os
import sqlite3
from collections.abc import Iterator

from fastapi import Request

DEFAULT_DB_PATH = "todo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
"""


def resolve_db_path(db_path: str | os.PathLike | None) -> str:
    if db_path is not None:
        return str(db_path)
    return os.environ.get("TODO_DB_PATH", DEFAULT_DB_PATH)


def connect(db_path: str) -> sqlite3.Connection:
    # FastAPI runs sync dependencies and routes in a thread pool, possibly on
    # different threads within one request.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    """One connection per request: commit on success, roll back on error."""
    conn = connect(request.app.state.db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
