"""Pydantic models for the notes resource."""

from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    """Fields accepted from a client when writing a note."""

    title: str
    body: str


class NoteRead(BaseModel):
    """Fields returned to a client for a stored note."""

    id: int
    title: str
    body: str
    created_at: datetime
