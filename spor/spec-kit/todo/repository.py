"""Every SQL statement in the application.

Lookups raise NotFoundError rather than returning None, so no caller has to
remember to check, and a missing row cannot reach a response model.
"""

import sqlite3
from typing import Any

from todo.errors import list_not_found, todo_not_found, todo_not_in_list

# --- lists ------------------------------------------------------------------


def create_list(conn: sqlite3.Connection, name: str) -> dict[str, Any]:
    cursor = conn.execute("INSERT INTO lists (name) VALUES (?)", (name,))
    conn.commit()
    return get_list(conn, int(cursor.lastrowid))


def get_list(conn: sqlite3.Connection, list_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT id, name FROM lists WHERE id = ?", (list_id,)).fetchone()
    if row is None:
        raise list_not_found(list_id)
    return dict(row)


def list_lists(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT id, name FROM lists ORDER BY id").fetchall()
    return [dict(row) for row in rows]


# --- todos ------------------------------------------------------------------


def create_todo(
    conn: sqlite3.Connection, list_id: int, title: str, done: bool
) -> dict[str, Any]:
    # Resolve the list first: a todo for a list that does not exist is a 404,
    # and nothing is written.
    get_list(conn, list_id)
    cursor = conn.execute(
        "INSERT INTO todos (title, done, list_id) VALUES (?, ?, ?)",
        (title, int(done), list_id),
    )
    conn.commit()
    return get_todo(conn, int(cursor.lastrowid))


def get_todo(conn: sqlite3.Connection, todo_id: int) -> dict[str, Any]:
    row = conn.execute(
        "SELECT id, title, done, list_id FROM todos WHERE id = ?", (todo_id,)
    ).fetchone()
    if row is None:
        raise todo_not_found(todo_id)
    return dict(row)


def list_todos(conn: sqlite3.Connection, list_id: int) -> list[dict[str, Any]]:
    # A missing list is a 404; an existing empty one is an empty collection.
    get_list(conn, list_id)
    rows = conn.execute(
        "SELECT id, title, done, list_id FROM todos WHERE list_id = ? ORDER BY id",
        (list_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_todo_in_list(
    conn: sqlite3.Connection, list_id: int, todo_id: int
) -> dict[str, Any]:
    """Read a todo through a list, which must be the list it belongs to.

    Membership is the query rather than a second lookup, so it cannot race and
    the nested path cannot be bypassed.
    """
    get_list(conn, list_id)
    row = conn.execute(
        "SELECT id, title, done, list_id FROM todos WHERE id = ? AND list_id = ?",
        (todo_id, list_id),
    ).fetchone()
    if row is None:
        raise todo_not_in_list(todo_id, list_id)
    return dict(row)


def update_list(conn: sqlite3.Connection, list_id: int, name: str) -> dict[str, Any]:
    get_list(conn, list_id)
    conn.execute("UPDATE lists SET name = ? WHERE id = ?", (name, list_id))
    conn.commit()
    return get_list(conn, list_id)


def delete_list(conn: sqlite3.Connection, list_id: int) -> None:
    get_list(conn, list_id)
    # The todos go with it through ON DELETE CASCADE, not through a second
    # statement here that could half-succeed.
    conn.execute("DELETE FROM lists WHERE id = ?", (list_id,))
    conn.commit()


def update_todo(
    conn: sqlite3.Connection, todo_id: int, fields: dict[str, Any]
) -> dict[str, Any]:
    """Write only the fields the caller actually sent."""
    get_todo(conn, todo_id)
    columns = {"title": str, "done": int}
    assignments = [f"{name} = ?" for name in fields if name in columns]
    values = [columns[name](fields[name]) for name in fields if name in columns]
    if assignments:
        conn.execute(
            f"UPDATE todos SET {', '.join(assignments)} WHERE id = ?",
            (*values, todo_id),
        )
        conn.commit()
    return get_todo(conn, todo_id)


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> None:
    get_todo(conn, todo_id)
    conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()


def move_todo(
    conn: sqlite3.Connection, todo_id: int, list_id: int
) -> dict[str, Any]:
    """Move a todo to another list, keeping its identifier, title and status.

    The todo is resolved before the destination, so a missing destination
    reports the list rather than the todo the caller already knows exists.
    """
    get_todo(conn, todo_id)
    get_list(conn, list_id)
    conn.execute("UPDATE todos SET list_id = ? WHERE id = ?", (list_id, todo_id))
    conn.commit()
    return get_todo(conn, todo_id)
