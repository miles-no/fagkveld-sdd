"""Inngang for uvicorn: `make run APP=todo_api.app:app`."""

from .main import create_app

app = create_app()
