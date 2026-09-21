"""HTTP routes for the notes resource."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db import get_connection
from app.notes.models import NoteCreate, NoteRead
from app.notes.repository import NoteRepository

router = APIRouter(prefix="/notes", tags=["notes"])

NOT_FOUND = "Note not found"


def get_repository(
    connection: Annotated[sqlite3.Connection, Depends(get_connection)],
) -> NoteRepository:
    """Build the repository for one request."""
    return NoteRepository(connection)


Repository = Annotated[NoteRepository, Depends(get_repository)]


@router.get("", response_model=list[NoteRead], status_code=status.HTTP_200_OK)
def list_notes(repository: Repository) -> list[NoteRead]:
    """Return every note."""
    return repository.list_all()


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, repository: Repository) -> NoteRead:
    """Create a note."""
    return repository.create(payload)


@router.get("/{note_id}", response_model=NoteRead, status_code=status.HTTP_200_OK)
def get_note(note_id: int, repository: Repository) -> NoteRead:
    """Return one note."""
    note = repository.get(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return note


@router.put("/{note_id}", response_model=NoteRead, status_code=status.HTTP_200_OK)
def replace_note(note_id: int, payload: NoteCreate, repository: Repository) -> NoteRead:
    """Overwrite one note."""
    note = repository.replace(note_id, payload)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, repository: Repository) -> None:
    """Delete one note."""
    if not repository.delete(note_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
