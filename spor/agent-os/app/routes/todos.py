"""Ruter for gjøremål.

Gjøremål hentes og opprettes under sin liste, fordi det er der nøstingen
betyr noe. Et enkelt gjøremål ligger flatt på ``/todos/{id}``, slik at
URL-en ikke endrer seg når gjøremålet flyttes til en annen liste.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, status

from app import db
from app.dependencies import Connection
from app.models import Todo, TodoCreate, TodoUpdate
from app.routes.lists import find_list

router = APIRouter(tags=["gjøremål"])


def find_todo(conn: sqlite3.Connection, todo_id: int) -> dict:
    """Henter gjøremålet, eller svarer 404 hvis det ikke finnes."""
    row = db.get_todo(conn, todo_id)
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Gjøremål {todo_id} finnes ikke"
        )
    return row


@router.get("/lists/{list_id}/todos", response_model=list[Todo])
def hent_gjoremal_i_liste(
    list_id: int, conn: Connection
) -> list[dict]:
    # En liste som ikke finnes er 404, ikke en tom liste. De to betyr
    # forskjellige ting, og klienten skal kunne skille dem.
    find_list(conn, list_id)
    return db.todos_in_list(conn, list_id)


@router.post(
    "/lists/{list_id}/todos",
    response_model=Todo,
    status_code=status.HTTP_201_CREATED,
)
def opprett_gjoremal(
    list_id: int,
    payload: TodoCreate,
    conn: Connection,
) -> dict:
    # list_id kommer fra stien, aldri fra kroppen.
    find_list(conn, list_id)
    return db.create_todo(conn, list_id, payload.title, payload.done)


@router.get("/todos/{todo_id}", response_model=Todo)
def hent_gjoremal(
    todo_id: int, conn: Connection
) -> dict:
    return find_todo(conn, todo_id)


@router.patch("/todos/{todo_id}", response_model=Todo)
def endre_gjoremal(
    todo_id: int,
    payload: TodoUpdate,
    conn: Connection,
) -> dict | None:
    find_todo(conn, todo_id)
    fields = payload.model_dump(exclude_unset=True)
    if "list_id" in fields:
        # Å flytte er å endre hvilken liste gjøremålet peker på. Målisten
        # slås opp her, så et forsøk på å flytte til noe som ikke finnes
        # blir en 404 og ikke en fremmednøkkelfeil fra databasen.
        find_list(conn, fields["list_id"])
    return db.update_todo(conn, todo_id, fields)


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def slett_gjoremal(
    todo_id: int, conn: Connection
) -> None:
    find_todo(conn, todo_id)
    db.delete_todo(conn, todo_id)
