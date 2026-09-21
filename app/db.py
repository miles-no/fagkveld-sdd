"""SQLite connection handling shared by every resource."""

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", "notes.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    """Open a connection that returns rows accessible by column name."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise() -> None:
    """Create the tables that do not exist yet."""
    connection = connect()
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()


def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection scoped to a single request."""
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
