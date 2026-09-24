import sqlite3

from todo_api import repository
from todo_api.errors import NotFoundError
from todo_api.schemas import ListCreate, ListRead


def create_list(conn: sqlite3.Connection, data: ListCreate) -> ListRead:
    return repository.create_list(conn, data.name)


def get_list(conn: sqlite3.Connection, list_id: int) -> ListRead:
    found = repository.get_list(conn, list_id)
    if found is None:
        raise NotFoundError("List", list_id)
    return found


def get_lists(conn: sqlite3.Connection) -> list[ListRead]:
    return repository.get_lists(conn)
