"""The application: wiring, startup, and the one not-found handler."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from todo.db import init_db
from todo.errors import NotFoundError, not_found_handler
from todo.routers import lists, todos


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="Todo Lists API",
    description="Lists and the todos inside them.",
    lifespan=lifespan,
)

app.add_exception_handler(NotFoundError, not_found_handler)
app.include_router(lists.router)
app.include_router(todos.router)
