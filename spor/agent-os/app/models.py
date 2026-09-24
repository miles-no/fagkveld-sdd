"""Pydantic-modellene for forespørsler og svar.

Listemodellen heter ``TodoList`` og ikke ``List``, fordi ``list`` er
innebygd og kolliderer i typeannotasjoner.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class PartialUpdate(BaseModel):
    """Felles regler for PATCH-kroppene.

    Et felt som utelates, endres ikke. Eksplisitt ``null`` er derimot ikke
    en gyldig verdi — ingen av kolonnene i databasen tillater NULL — så den
    avvises med 422 i stedet for å bli stille ignorert.
    """

    @model_validator(mode="before")
    @classmethod
    def reject_null(cls, data: Any) -> Any:
        if isinstance(data, dict):
            nulls = sorted(key for key, value in data.items() if value is None)
            if nulls:
                raise ValueError(f"Feltet kan ikke være null: {', '.join(nulls)}")
        return data


# --- lister -----------------------------------------------------------------


class TodoListCreate(BaseModel):
    name: str = Field(min_length=1)


class TodoListUpdate(PartialUpdate):
    name: str | None = Field(default=None, min_length=1)


class TodoList(BaseModel):
    id: int
    name: str


# --- gjøremål ---------------------------------------------------------------


class TodoCreate(BaseModel):
    title: str = Field(min_length=1)
    done: bool = False


class TodoUpdate(PartialUpdate):
    title: str | None = Field(default=None, min_length=1)
    done: bool | None = None
    list_id: int | None = None


class Todo(BaseModel):
    id: int
    title: str
    done: bool
    list_id: int
