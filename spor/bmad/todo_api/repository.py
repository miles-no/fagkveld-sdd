import sqlite3

from todo_api.schemas import ListRead


def _to_list(row: sqlite3.Row) -> ListRead:
    return ListRead(id=row["id"], name=row["name"])


def create_list(conn: sqlite3.Connection, name: str) -> ListRead:
    cursor = conn.execute("INSERT INTO lists (name) VALUES (?)", (name,))
    return ListRead(id=cursor.lastrowid, name=name)


def get_list(conn: sqlite3.Connection, list_id: int) -> ListRead | None:
    row = conn.execute("SELECT id, name FROM lists WHERE id = ?", (list_id,)).fetchone()
    return _to_list(row) if row else None


def get_lists(conn: sqlite3.Connection) -> list[ListRead]:
    rows = conn.execute("SELECT id, name FROM lists ORDER BY id").fetchall()
    return [_to_list(row) for row in rows]
