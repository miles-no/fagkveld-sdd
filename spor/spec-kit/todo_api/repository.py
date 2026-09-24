"""All SQL. Parameteriserte spørringer; ingen verdi interpoleres inn i en
setning, og kolonnenavn i SET-klausuler kommer fra faste hvitlister.
"""

import sqlite3

from todo_api.errors import NotFoundError
from todo_api.models import (
    Todo,
    TodoCreate,
    TodoList,
    TodoListCreate,
    TodoListUpdate,
    TodoUpdate,
)

TODO_FIELDS = "id, title, done, list_id"

# Hvitliste. Kolonnenavn i en SET-klausul kommer herfra, aldri fra klientens
# nøkler — verdier er parameteriserte, men kolonnenavn kan ikke være det.
TODO_UPDATABLE = ("title", "done")
LIST_UPDATABLE = ("name",)


def _to_list(row: sqlite3.Row) -> TodoList:
    return TodoList(id=row["id"], name=row["name"])


def _to_todo(row: sqlite3.Row) -> Todo:
    return Todo(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
        list_id=row["list_id"],
    )


def require_list(conn: sqlite3.Connection, list_id: int) -> None:
    """Kast NotFoundError hvis listen ikke finnes.

    Sjekken gir et presist 404 der fremmednøkkelen ellers ville gitt en
    IntegrityError — og dermed en 500 — for det samme.
    """
    row = conn.execute("SELECT 1 FROM lists WHERE id = ?", (list_id,)).fetchone()
    if row is None:
        raise NotFoundError("list", list_id)


# --- lister -------------------------------------------------------------------


def create_list(conn: sqlite3.Connection, data: TodoListCreate) -> TodoList:
    with conn:
        row = conn.execute(
            "INSERT INTO lists(name) VALUES(?) RETURNING id, name",
            (data.name,),
        ).fetchone()
    return _to_list(row)


def all_lists(conn: sqlite3.Connection) -> list[TodoList]:
    rows = conn.execute("SELECT id, name FROM lists ORDER BY id").fetchall()
    return [_to_list(row) for row in rows]


def get_list(conn: sqlite3.Connection, list_id: int) -> TodoList:
    row = conn.execute("SELECT id, name FROM lists WHERE id = ?", (list_id,)).fetchone()
    if row is None:
        raise NotFoundError("list", list_id)
    return _to_list(row)


def update_list(conn: sqlite3.Connection, list_id: int, data: TodoListUpdate) -> TodoList:
    endringer = data.model_dump(exclude_unset=True)
    if not endringer:
        return get_list(conn, list_id)

    kolonner = [navn for navn in LIST_UPDATABLE if navn in endringer]
    sett = ", ".join(f"{navn} = ?" for navn in kolonner)
    with conn:
        row = conn.execute(
            f"UPDATE lists SET {sett} WHERE id = ? RETURNING id, name",
            (*[endringer[navn] for navn in kolonner], list_id),
        ).fetchone()
    if row is None:
        raise NotFoundError("list", list_id)
    return _to_list(row)


def delete_list(conn: sqlite3.Connection, list_id: int) -> None:
    """Gjøremålene i listen forsvinner med den, via ON DELETE CASCADE."""
    with conn:
        markør = conn.execute("DELETE FROM lists WHERE id = ?", (list_id,))
    if markør.rowcount == 0:
        raise NotFoundError("list", list_id)


# --- gjøremål -----------------------------------------------------------------


def create_todo(conn: sqlite3.Connection, list_id: int, data: TodoCreate) -> Todo:
    require_list(conn, list_id)
    with conn:
        row = conn.execute(
            "INSERT INTO todos(title, done, list_id) VALUES(?, ?, ?)"
            " RETURNING id, title, done, list_id",
            (data.title, int(data.done), list_id),
        ).fetchone()
    return _to_todo(row)


def todos_for_list(conn: sqlite3.Connection, list_id: int) -> list[Todo]:
    require_list(conn, list_id)
    rows = conn.execute(
        f"SELECT {TODO_FIELDS} FROM todos WHERE list_id = ? ORDER BY id",
        (list_id,),
    ).fetchall()
    return [_to_todo(row) for row in rows]


def get_todo(conn: sqlite3.Connection, todo_id: int) -> Todo:
    row = conn.execute(
        f"SELECT {TODO_FIELDS} FROM todos WHERE id = ?", (todo_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError("todo", todo_id)
    return _to_todo(row)


def update_todo(conn: sqlite3.Connection, todo_id: int, data: TodoUpdate) -> Todo:
    endringer = data.model_dump(exclude_unset=True)
    if not endringer:
        return get_todo(conn, todo_id)

    kolonner = [navn for navn in TODO_UPDATABLE if navn in endringer]
    verdier = [
        int(endringer[navn]) if navn == "done" else endringer[navn] for navn in kolonner
    ]
    sett = ", ".join(f"{navn} = ?" for navn in kolonner)
    with conn:
        row = conn.execute(
            f"UPDATE todos SET {sett} WHERE id = ? RETURNING {TODO_FIELDS}",
            (*verdier, todo_id),
        ).fetchone()
    if row is None:
        raise NotFoundError("todo", todo_id)
    return _to_todo(row)


def move_todo(conn: sqlite3.Connection, todo_id: int, list_id: int) -> Todo:
    """Flytt gjøremålet til en annen liste.

    Rekkefølgen på sjekkene er kontraktfestet: finnes ikke gjøremålet, er det
    det klienten skal få vite — ikke at mållisten også mangler.
    """
    get_todo(conn, todo_id)
    require_list(conn, list_id)
    with conn:
        row = conn.execute(
            f"UPDATE todos SET list_id = ? WHERE id = ? RETURNING {TODO_FIELDS}",
            (list_id, todo_id),
        ).fetchone()
    return _to_todo(row)


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> None:
    with conn:
        markør = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    if markør.rowcount == 0:
        raise NotFoundError("todo", todo_id)
