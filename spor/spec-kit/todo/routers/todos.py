"""Routes under /todos: reading, changing, deleting and moving a todo.

A todo is addressable by its own identifier here; the /lists routes cover the
same todos in the context of the list that holds them.
"""

from fastapi import APIRouter, status

from todo import repository
from todo.db import DbConn
from todo.schemas import TodoMove, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, conn: DbConn):
    return repository.get_todo(conn, todo_id)


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, payload: TodoUpdate, conn: DbConn):
    # exclude_unset keeps an omitted field out of the UPDATE; exclude_none keeps
    # an explicit null from blanking a column.
    fields = payload.model_dump(exclude_unset=True, exclude_none=True)
    return repository.update_todo(conn, todo_id, fields)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, conn: DbConn) -> None:
    repository.delete_todo(conn, todo_id)


@router.post("/{todo_id}/move", response_model=TodoOut)
def move_todo(todo_id: int, payload: TodoMove, conn: DbConn):
    return repository.move_todo(conn, todo_id, payload.list_id)
