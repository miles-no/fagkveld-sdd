"""Database access for the notes resource."""

import sqlite3
from datetime import UTC, datetime

from app.notes.models import NoteCreate, NoteRead

COLUMNS = "id, title, body, created_at"


class NoteRepository:
    """Every SQL statement touching the notes table lives here."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Bind the repository to one connection.

        Args:
            connection: Open connection, scoped to a single request.
        """
        self._connection = connection

    def list_all(self) -> list[NoteRead]:
        """Return every note, newest first."""
        rows = self._connection.execute(
            f"SELECT {COLUMNS} FROM notes ORDER BY id DESC"
        ).fetchall()
        return [NoteRead(**dict(row)) for row in rows]

    def get(self, note_id: int) -> NoteRead | None:
        """Return one note, or None when no note has that id."""
        row = self._connection.execute(
            f"SELECT {COLUMNS} FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return NoteRead(**dict(row)) if row else None

    def create(self, payload: NoteCreate) -> NoteRead:
        """Insert a note and return it as stored."""
        created_at = datetime.now(UTC)
        cursor = self._connection.execute(
            "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
            (payload.title, payload.body, created_at.isoformat()),
        )
        self._connection.commit()
        return NoteRead(
            id=int(cursor.lastrowid or 0),
            title=payload.title,
            body=payload.body,
            created_at=created_at,
        )

    def replace(self, note_id: int, payload: NoteCreate) -> NoteRead | None:
        """Overwrite a note, or return None when no note has that id."""
        cursor = self._connection.execute(
            "UPDATE notes SET title = ?, body = ? WHERE id = ?",
            (payload.title, payload.body, note_id),
        )
        self._connection.commit()
        return self.get(note_id) if cursor.rowcount else None

    def delete(self, note_id: int) -> bool:
        """Delete a note and report whether a row was removed."""
        cursor = self._connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self._connection.commit()
        return cursor.rowcount > 0
