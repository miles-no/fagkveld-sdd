import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, status

from todo_api import service
from todo_api.db import get_connection
from todo_api.schemas import ListCreate, ListRead

router = APIRouter()

# scope="function" commits before the response is sent, so a 2xx means the data is stored.
Connection = Annotated[sqlite3.Connection, Depends(get_connection, scope="function")]


@router.post("/lists", status_code=status.HTTP_201_CREATED)
def create_list(data: ListCreate, conn: Connection) -> ListRead:
    return service.create_list(conn, data)


@router.get("/lists")
def get_lists(conn: Connection) -> list[ListRead]:
    return service.get_lists(conn)


@router.get("/lists/{list_id}")
def get_list(list_id: int, conn: Connection) -> ListRead:
    return service.get_list(conn, list_id)
