"""API-ets kontrakt. Rader fra databasen konverteres hit før de forlater
datalaget, slik at sqlite3.Row aldri lekker ut i rutene.
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator

NAME_MAX = 200
TITLE_MAX = 500

Name = Annotated[str, StringConstraints(max_length=NAME_MAX)]
Title = Annotated[str, StringConstraints(max_length=TITLE_MAX)]


def _trimmed(value: str | None) -> str | None:
    """Trim og avvis tomt. min_length alene slipper "   " gjennom."""
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        raise ValueError("kan ikke være tom eller kun blanke tegn")
    return stripped


class _Strict(BaseModel):
    """Ukjente felt avvises framfor å ignoreres stille."""

    model_config = ConfigDict(extra="forbid")


class _PartialUpdate(_Strict):
    """Delvis oppdatering: felt som ikke sendes, forblir uendret.

    None er her «ikke sendt», ikke «sett til ingenting». Sendes et felt
    eksplisitt som null, er det ugyldig inndata — kolonnene er NOT NULL, så
    alternativet ville vært en databasefeil og dermed en 500.
    """

    @model_validator(mode="after")
    def _avvis_eksplisitt_null(self) -> "_PartialUpdate":
        for felt in self.model_fields_set:
            if getattr(self, felt) is None:
                raise ValueError(f"{felt} kan ikke settes til null")
        return self


class TodoListCreate(_Strict):
    name: Name

    _trim = field_validator("name")(_trimmed)


class TodoListUpdate(_PartialUpdate):
    name: Name | None = None

    _trim = field_validator("name")(_trimmed)


class TodoList(_Strict):
    id: int
    name: str


class TodoCreate(_Strict):
    title: Title
    done: bool = False

    _trim = field_validator("title")(_trimmed)


class TodoUpdate(_PartialUpdate):
    title: Title | None = None
    done: bool | None = None

    _trim = field_validator("title")(_trimmed)


class MoveRequest(_Strict):
    list_id: int


class Todo(_Strict):
    id: int
    title: str
    done: bool
    list_id: int
