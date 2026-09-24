"""Routes under /lists, including the todos a list holds."""

from fastapi import APIRouter, status

from todo import repository
from todo.db import DbConn
from todo.schemas import ListCreate, ListOut, ListUpdate, TodoCreate, TodoOut

router = APIRouter(prefix="/lists", tags=["lists"])


@router.post("", response_model=ListOut, status_code=status.HTTP_201_CREATED)
def create_list(payload: ListCreate, conn: DbConn):
    return repository.create_list(conn, payload.name)


@router.get("", response_model=list[ListOut])
def get_lists(conn: DbConn):
    return repository.list_lists(conn)


@router.get("/{list_id}", response_model=ListOut)
def get_list(list_id: int, conn: DbConn):
    return repository.get_list(conn, list_id)


@router.patch("/{list_id}", response_model=ListOut)
def update_list(list_id: int, payload: ListUpdate, conn: DbConn):
    return repository.update_list(conn, list_id, payload.name)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(list_id: int, conn: DbConn) -> None:
    repository.delete_list(conn, list_id)


@router.get("/{list_id}/todos", response_model=list[TodoOut])
def get_list_todos(list_id: int, conn: DbConn):
    return repository.list_todos(conn, list_id)


@router.post(
    "/{list_id}/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED
)
def create_todo(list_id: int, payload: TodoCreate, conn: DbConn):
    return repository.create_todo(conn, list_id, payload.title, payload.done)


@router.get("/{list_id}/todos/{todo_id}", response_model=TodoOut)
def get_list_todo(list_id: int, todo_id: int, conn: DbConn):
    """Reading a todo here checks it really belongs to this list."""
    return repository.get_todo_in_list(conn, list_id, todo_id)
