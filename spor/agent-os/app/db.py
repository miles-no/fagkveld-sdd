"""Datalaget. Eneste fil i prosjektet som inneholder SQL.

Funksjonene her kjenner ikke HTTP. De returnerer rader eller ``None``, og
overlater til rutelaget å bestemme hva fraværet av en rad betyr.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from pathlib import Path

DB_ENV_VAR = "TODO_DB_PATH"
DEFAULT_DB_PATH = "todo.db"

LIST_COLUMNS = "id, name"
TODO_COLUMNS = "id, title, done, list_id"

SCHEMA = """
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0,
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);
"""


def database_path() -> Path:
    """Stien til databasefilen.

    Leses ved hvert kall og ikke ved import, slik at en test kan peke den
    mot sin egen midlertidige fil før applikasjonen starter.
    """
    return Path(os.environ.get(DB_ENV_VAR, DEFAULT_DB_PATH))


def connect() -> sqlite3.Connection:
    """Åpner en tilkobling mot databasefilen på disk."""
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    # SQLite har fremmednøkler av som standard, og de må slås på per
    # tilkobling. Uten dette er list_id bare et tall uten garantier.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema() -> None:
    """Oppretter tabellene hvis de ikke finnes. Kjøres ved oppstart."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def get_connection() -> Iterator[sqlite3.Connection]:
    """FastAPI-avhengighet: én tilkobling per forespørsel."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _one(cursor: sqlite3.Cursor) -> dict | None:
    """Første rad som dict, eller ``None`` når det ikke er noen.

    ``sqlite3.Row`` er ikke en mapping, og Pydantic kan ikke validere den.
    Konverteringen hører hjemme her, så rutelaget slipper å vite det.
    """
    row = cursor.fetchone()
    return dict(row) if row is not None else None


def _all(cursor: sqlite3.Cursor) -> list[dict]:
    return [dict(row) for row in cursor.fetchall()]


def _assignments(fields: dict, allowed: set[str]) -> str:
    """Bygger SET-delen av en UPDATE.

    Kolonnenavn kan ikke parameteriseres i SQL, så de sjekkes mot en
    hviteliste i stedet. Verdiene bindes som vanlig med ?.
    """
    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"Ukjente kolonner: {', '.join(sorted(unknown))}")
    return ", ".join(f"{column} = ?" for column in fields)


# --- lister -----------------------------------------------------------------


def create_list(conn: sqlite3.Connection, name: str) -> dict:
    return _one(
        conn.execute(
            f"INSERT INTO lists (name) VALUES (?) RETURNING {LIST_COLUMNS}",
            (name,),
        )
    )


def all_lists(conn: sqlite3.Connection) -> list[dict]:
    return _all(conn.execute(f"SELECT {LIST_COLUMNS} FROM lists ORDER BY id"))


def get_list(conn: sqlite3.Connection, list_id: int) -> dict | None:
    return _one(
        conn.execute(f"SELECT {LIST_COLUMNS} FROM lists WHERE id = ?", (list_id,))
    )


def update_list(conn: sqlite3.Connection, list_id: int, fields: dict) -> dict | None:
    if not fields:
        return get_list(conn, list_id)
    return _one(
        conn.execute(
            f"UPDATE lists SET {_assignments(fields, {'name'})} "
            f"WHERE id = ? RETURNING {LIST_COLUMNS}",
            (*fields.values(), list_id),
        )
    )


def delete_list(conn: sqlite3.Connection, list_id: int) -> bool:
    """Sletter listen. Gjøremålene i den forsvinner via ON DELETE CASCADE."""
    return conn.execute("DELETE FROM lists WHERE id = ?", (list_id,)).rowcount > 0


# --- gjøremål ---------------------------------------------------------------


def create_todo(conn: sqlite3.Connection, list_id: int, title: str, done: bool) -> dict:
    return _one(
        conn.execute(
            f"INSERT INTO todos (title, done, list_id) VALUES (?, ?, ?) "
            f"RETURNING {TODO_COLUMNS}",
            (title, done, list_id),
        )
    )


def todos_in_list(conn: sqlite3.Connection, list_id: int) -> list[dict]:
    return _all(
        conn.execute(
            f"SELECT {TODO_COLUMNS} FROM todos WHERE list_id = ? ORDER BY id",
            (list_id,),
        )
    )


def get_todo(conn: sqlite3.Connection, todo_id: int) -> dict | None:
    return _one(
        conn.execute(f"SELECT {TODO_COLUMNS} FROM todos WHERE id = ?", (todo_id,))
    )


def update_todo(conn: sqlite3.Connection, todo_id: int, fields: dict) -> dict | None:
    if not fields:
        return get_todo(conn, todo_id)
    allowed = {"title", "done", "list_id"}
    return _one(
        conn.execute(
            f"UPDATE todos SET {_assignments(fields, allowed)} "
            f"WHERE id = ? RETURNING {TODO_COLUMNS}",
            (*fields.values(), todo_id),
        )
    )


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    return conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,)).rowcount > 0
