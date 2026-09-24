"""Tilkobling til SQLite og oppretting av skjemaet."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request

SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY,
    title   TEXT    NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_todos_list_id ON todos(list_id);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    """Åpne en tilkobling med radfabrikk og fremmednøkler slått på.

    Pragmaet er per tilkobling og lagres ikke i filen. Uten det er
    ON DELETE CASCADE og REFERENCES i skjemaet ren dokumentasjon.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(path: str | Path) -> None:
    """Opprett tabellene hvis de ikke finnes. Trygg å kjøre på nytt."""
    conn = connect(path)
    try:
        with conn:
            conn.executescript(SCHEMA)
    finally:
        conn.close()


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    """Avhengighet som gir én tilkobling per forespørsel."""
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()
