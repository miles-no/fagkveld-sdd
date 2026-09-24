"""Applikasjonen: oppretter skjemaet ved oppstart og monterer rutene.

Kjøres fra spor/agent-os med:

    make run APP=app.main:app
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import create_schema
from app.routes import lists, todos


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_schema()
    yield


app = FastAPI(
    title="Gjøremål",
    description="Et API for gjøremål og lister.",
    lifespan=lifespan,
)

app.include_router(lists.router)
app.include_router(todos.router)
