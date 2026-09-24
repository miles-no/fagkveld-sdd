"""Applikasjonsfabrikk."""

import os
from pathlib import Path

from fastapi import FastAPI

from todo_api.db import init_schema
from todo_api.errors import register_handlers
from todo_api.routers import lists, todos

DEFAULT_DB_PATH = "todo.db"


def create_app(db_path: str | Path | None = None) -> FastAPI:
    """Bygg en applikasjon mot én databasefil.

    Fabrikken finnes for at hver test skal kunne kjøre mot sin egen fil, og for
    at to apper etter hverandre mot samme fil skal se de samme dataene.
    """
    path = Path(db_path or os.environ.get("TODO_DB_PATH", DEFAULT_DB_PATH))
    init_schema(path)

    app = FastAPI(
        title="TODO-API",
        description="Gjøremål og lister.",
        version="1.0.0",
    )
    app.state.db_path = path
    register_handlers(app)
    app.include_router(lists.router)
    app.include_router(todos.router)
    return app


app = create_app()
