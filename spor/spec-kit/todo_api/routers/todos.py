"""Endepunkter for gjøremål, inkludert de listescopede."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, status

from todo_api import repository
from todo_api.db import get_conn
from todo_api.models import MoveRequest, Todo, TodoCreate, TodoUpdate

router = APIRouter(tags=["todos"])

Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


@router.post(
    "/lists/{list_id}/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
)
def opprett_gjoremal(list_id: int, data: TodoCreate, conn: Conn) -> Todo:
    return repository.create_todo(conn, list_id, data)


@router.get("/lists/{list_id}/todos", response_model=list[Todo])
def gjoremal_i_liste(list_id: int, conn: Conn) -> list[Todo]:
    return repository.todos_for_list(conn, list_id)


@router.get("/todos/{todo_id}", response_model=Todo)
def hent_gjoremal(todo_id: int, conn: Conn) -> Todo:
    return repository.get_todo(conn, todo_id)


@router.patch("/todos/{todo_id}", response_model=Todo)
def endre_gjoremal(todo_id: int, data: TodoUpdate, conn: Conn) -> Todo:
    return repository.update_todo(conn, todo_id, data)


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def slett_gjoremal(todo_id: int, conn: Conn) -> None:
    repository.delete_todo(conn, todo_id)


@router.post("/todos/{todo_id}/move", response_model=Todo)
def flytt_gjoremal(todo_id: int, data: MoveRequest, conn: Conn) -> Todo:
    return repository.move_todo(conn, todo_id, data.list_id)
