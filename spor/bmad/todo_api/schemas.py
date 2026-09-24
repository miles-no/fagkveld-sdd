from typing import Annotated

from pydantic import BaseModel, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ListCreate(BaseModel):
    name: NonEmptyStr


class ListRead(BaseModel):
    id: int
    name: str
