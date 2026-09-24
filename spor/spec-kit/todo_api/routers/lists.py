"""Endepunkter for lister."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, status

from todo_api import repository
from todo_api.db import get_conn
from todo_api.models import TodoList, TodoListCreate, TodoListUpdate

router = APIRouter(prefix="/lists", tags=["lists"])

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


@router.post("", response_model=TodoList, status_code=status.HTTP_201_CREATED)
def opprett_liste(data: TodoListCreate, conn: Conn) -> TodoList:
    return repository.create_list(conn, data)


@router.get("", response_model=list[TodoList])
def hent_alle_lister(conn: Conn) -> list[TodoList]:
    return repository.all_lists(conn)


@router.get("/{list_id}", response_model=TodoList)
def hent_liste(list_id: int, conn: Conn) -> TodoList:
    return repository.get_list(conn, list_id)


@router.patch("/{list_id}", response_model=TodoList)
def endre_liste(list_id: int, data: TodoListUpdate, conn: Conn) -> TodoList:
    return repository.update_list(conn, list_id, data)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def slett_liste(list_id: int, conn: Conn) -> None:
    repository.delete_list(conn, list_id)
