"""Ruter for lister.

``find_list`` bor her fordi listen er ressursen denne modulen eier;
gjøremålsrutene importerer den når de trenger å slå opp en liste.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, status

from app import db
from app.dependencies import Connection
from app.models import TodoList, TodoListCreate, TodoListUpdate

router = APIRouter(prefix="/lists", tags=["lister"])


def find_list(conn: sqlite3.Connection, list_id: int) -> dict:
    """Henter listen, eller svarer 404 hvis den ikke finnes.

    At en liste ikke finnes er et normalt utfall, ikke en feil — derfor et
    oppslag med et forklarende svar, ikke et unntak som slipper gjennom.
    """
    row = db.get_list(conn, list_id)
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Liste {list_id} finnes ikke"
        )
    return row


@router.post("", response_model=TodoList, status_code=status.HTTP_201_CREATED)
def opprett_liste(
    payload: TodoListCreate, conn: Connection
) -> dict:
    return db.create_list(conn, payload.name)


@router.get("", response_model=list[TodoList])
def hent_lister(
    conn: Connection,
) -> list[dict]:
    return db.all_lists(conn)


@router.get("/{list_id}", response_model=TodoList)
def hent_liste(
    list_id: int, conn: Connection
) -> dict:
    return find_list(conn, list_id)


@router.patch("/{list_id}", response_model=TodoList)
def endre_liste(
    list_id: int,
    payload: TodoListUpdate,
    conn: Connection,
) -> dict | None:
    find_list(conn, list_id)
    return db.update_list(conn, list_id, payload.model_dump(exclude_unset=True))


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def slett_liste(
    list_id: int, conn: Connection
) -> None:
    find_list(conn, list_id)
    db.delete_list(conn, list_id)
