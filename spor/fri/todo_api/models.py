from pydantic import BaseModel, ConfigDict, Field

Name = Field(min_length=1, max_length=200)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ListCreate(_Strict):
    name: str = Name


class ListUpdate(_Strict):
    name: str = Name


class TodoList(BaseModel):
    id: int
    name: str


class TodoCreate(_Strict):
    title: str = Name
    list_id: int
    done: bool = False


class TodoUpdate(_Strict):
    """Delvis oppdatering. Å sette list_id flytter gjøremålet til en annen liste."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None
    list_id: int | None = None


class Todo(BaseModel):
    id: int
    title: str
    done: bool
    list_id: int
