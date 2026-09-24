import os
import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status

from . import repository as repo
from .db import Database
from .models import ListCreate, ListUpdate, Todo, TodoCreate, TodoList, TodoUpdate

DEFAULT_DB_PATH = "todo.db"


def _not_found(kind: str, id_: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"{kind} {id_} finnes ikke")


def create_app(db_path: str | None = None) -> FastAPI:
    db = Database(db_path or os.environ.get("TODO_DB", DEFAULT_DB_PATH))
    app = FastAPI(title="Gjøremål")

    def conn() -> Iterator[sqlite3.Connection]:
        with db.connect() as c:
            yield c

    Conn = Annotated[sqlite3.Connection, Depends(conn)]

    def require_list(c: sqlite3.Connection, list_id: int) -> TodoList:
        found = repo.get_list(c, list_id)
        if found is None:
            raise _not_found("Liste", list_id)
        return found

    # Lister

    @app.get("/lists")
    def list_lists(c: Conn) -> list[TodoList]:
        return repo.all_lists(c)

    @app.post("/lists", status_code=status.HTTP_201_CREATED)
    def create_list(body: ListCreate, c: Conn) -> TodoList:
        return repo.create_list(c, body.name)

    @app.get("/lists/{list_id}")
    def get_list(list_id: int, c: Conn) -> TodoList:
        return require_list(c, list_id)

    @app.patch("/lists/{list_id}")
    def update_list(list_id: int, body: ListUpdate, c: Conn) -> TodoList:
        updated = repo.rename_list(c, list_id, body.name)
        if updated is None:
            raise _not_found("Liste", list_id)
        return updated

    @app.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_list(list_id: int, c: Conn) -> Response:
        """Sletter lista og alle gjøremålene i den."""
        if not repo.delete_list(c, list_id):
            raise _not_found("Liste", list_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/lists/{list_id}/todos")
    def list_todos_in_list(list_id: int, c: Conn) -> list[Todo]:
        require_list(c, list_id)
        return repo.all_todos(c, list_id)

    # Gjøremål

    @app.get("/todos")
    def list_todos(c: Conn) -> list[Todo]:
        return repo.all_todos(c)

    @app.post("/todos", status_code=status.HTTP_201_CREATED)
    def create_todo(body: TodoCreate, c: Conn) -> Todo:
        require_list(c, body.list_id)
        return repo.create_todo(c, body)

    @app.get("/todos/{todo_id}")
    def get_todo(todo_id: int, c: Conn) -> Todo:
        found = repo.get_todo(c, todo_id)
        if found is None:
            raise _not_found("Gjøremål", todo_id)
        return found

    @app.patch("/todos/{todo_id}")
    def update_todo(todo_id: int, body: TodoUpdate, c: Conn) -> Todo:
        """Endrer tittel og/eller status. Sett `list_id` for å flytte til en annen liste."""
        if body.list_id is not None:
            require_list(c, body.list_id)
        updated = repo.update_todo(c, todo_id, body)
        if updated is None:
            raise _not_found("Gjøremål", todo_id)
        return updated

    @app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_todo(todo_id: int, c: Conn) -> Response:
        if not repo.delete_todo(c, todo_id):
            raise _not_found("Gjøremål", todo_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app
