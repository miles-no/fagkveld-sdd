"""Request and response bodies, and the input validation that goes with them.

Names and titles are stripped before the length check, so a whitespace-only
value fails rather than passing as a few characters of nothing.
"""

from typing import Annotated

from pydantic import BaseModel, StringConstraints, model_validator

Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ListCreate(BaseModel):
    name: Label


class ListUpdate(BaseModel):
    # Required rather than optional: a list has one mutable field, so an empty
    # body is already a 422 "field required" without a validator of its own.
    name: Label


class ListOut(BaseModel):
    id: int
    name: str


class TodoCreate(BaseModel):
    title: Label
    done: bool = False


class TodoUpdate(BaseModel):
    title: Label | None = None
    done: bool | None = None

    @model_validator(mode="after")
    def require_a_field(self) -> "TodoUpdate":
        """An update that changes nothing is a mistake, not a no-op."""
        if self.title is None and self.done is None:
            raise ValueError("provide 'title', 'done', or both")
        return self


class TodoMove(BaseModel):
    list_id: int


class TodoOut(BaseModel):
    id: int
    title: str
    done: bool
    list_id: int
