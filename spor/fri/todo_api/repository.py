import sqlite3

from .models import Todo, TodoCreate, TodoList, TodoUpdate


def _todo(row: sqlite3.Row) -> Todo:
    return Todo(id=row["id"], title=row["title"], done=bool(row["done"]), list_id=row["list_id"])


def _list(row: sqlite3.Row) -> TodoList:
    return TodoList(id=row["id"], name=row["name"])


# Lister


def all_lists(conn: sqlite3.Connection) -> list[TodoList]:
    return [_list(r) for r in conn.execute("SELECT id, name FROM lists ORDER BY id")]


def get_list(conn: sqlite3.Connection, list_id: int) -> TodoList | None:
    row = conn.execute("SELECT id, name FROM lists WHERE id = ?", (list_id,)).fetchone()
    return _list(row) if row else None


def create_list(conn: sqlite3.Connection, name: str) -> TodoList:
    cur = conn.execute("INSERT INTO lists (name) VALUES (?)", (name,))
    return TodoList(id=cur.lastrowid, name=name)


def rename_list(conn: sqlite3.Connection, list_id: int, name: str) -> TodoList | None:
    cur = conn.execute("UPDATE lists SET name = ? WHERE id = ?", (name, list_id))
    return TodoList(id=list_id, name=name) if cur.rowcount else None


def delete_list(conn: sqlite3.Connection, list_id: int) -> bool:
    return conn.execute("DELETE FROM lists WHERE id = ?", (list_id,)).rowcount > 0


# Gjøremål

_TODO_COLS = "SELECT id, title, done, list_id FROM todos"


def all_todos(conn: sqlite3.Connection, list_id: int | None = None) -> list[Todo]:
    if list_id is None:
        rows = conn.execute(f"{_TODO_COLS} ORDER BY id")
    else:
        rows = conn.execute(f"{_TODO_COLS} WHERE list_id = ? ORDER BY id", (list_id,))
    return [_todo(r) for r in rows]


def get_todo(conn: sqlite3.Connection, todo_id: int) -> Todo | None:
    row = conn.execute(f"{_TODO_COLS} WHERE id = ?", (todo_id,)).fetchone()
    return _todo(row) if row else None


def create_todo(conn: sqlite3.Connection, data: TodoCreate) -> Todo:
    cur = conn.execute(
        "INSERT INTO todos (title, done, list_id) VALUES (?, ?, ?)",
        (data.title, int(data.done), data.list_id),
    )
    return Todo(id=cur.lastrowid, **data.model_dump())


def update_todo(conn: sqlite3.Connection, todo_id: int, changes: TodoUpdate) -> Todo | None:
    current = get_todo(conn, todo_id)
    if current is None:
        return None
    updated = current.model_copy(update=changes.model_dump(exclude_none=True))
    conn.execute(
        "UPDATE todos SET title = ?, done = ?, list_id = ? WHERE id = ?",
        (updated.title, int(updated.done), updated.list_id, todo_id),
    )
    return updated


def delete_todo(conn: sqlite3.Connection, todo_id: int) -> bool:
    return conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,)).rowcount > 0
