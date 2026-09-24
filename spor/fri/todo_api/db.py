import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0,
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS todos_list_id ON todos(list_id);
"""


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:  # commit ved suksess, rollback ved unntak
                yield conn
        finally:
            conn.close()
