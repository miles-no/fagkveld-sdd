import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from todo_api.api import router
from todo_api.db import init_db, resolve_db_path
from todo_api.errors import NotFoundError


def create_app(db_path: str | os.PathLike | None = None) -> FastAPI:
    resolved_path = resolve_db_path(db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        init_db(resolved_path)
        yield

    app = FastAPI(title="Todo & Lists API", lifespan=lifespan)
    app.state.db_path = resolved_path
    app.include_router(router)

    @app.exception_handler(NotFoundError)
    async def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    return app


app = create_app()
