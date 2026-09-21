"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import initialise
from app.notes.router import router as notes_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create the database schema before the first request is served."""
    initialise()
    yield


app = FastAPI(title="Notes API", version="0.1.0", lifespan=lifespan)
app.include_router(notes_router)
