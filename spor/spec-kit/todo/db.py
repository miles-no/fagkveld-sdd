"""SQLite storage: where the file lives, how connections are made, what the schema is.

The database path is resolved from the package directory rather than the working
directory, so starting the app from elsewhere addresses the same file instead of
quietly creating a second one.
"""

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "todo.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_todos_list_id ON todos(list_id);
"""


def database_path() -> Path:
    """The SQLite file to use. Read on every call so tests can redirect it."""
    override = os.environ.get("TODO_DB_PATH")
    return Path(override) if override else _DEFAULT_DB_PATH


def connect() -> sqlite3.Connection:
    """Open a connection with row access by name and foreign keys enforced.

    SQLite leaves foreign key enforcement off by default and silently ignores
    the constraint without the pragma, so it is set here where no caller can
    skip it -- the cascade from a deleted list to its todos depends on it.
    """
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create the schema if it is not already there. Safe to run on every start."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_db() -> Iterator[sqlite3.Connection]:
    """One connection per request.

    FastAPI runs synchronous handlers in a thread pool, so a shared module-level
    connection would be used across threads. Opening a SQLite file is cheap.
    """
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


# Routers annotate their connection parameter with this rather than calling
# Depends() in a default argument.
DbConn = Annotated[sqlite3.Connection, Depends(get_db)]
