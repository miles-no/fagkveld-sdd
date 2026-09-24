"""Not-found handling, in one place.

Asking for something that does not exist is a normal outcome, not a fault. The
repository raises NotFoundError; the handler registered in todo.main renders it
as a 404. No route implements this itself, so a new route inherits the behaviour.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """A list or todo named by the request does not exist."""

    def __init__(self, message: str, *, resource: str) -> None:
        super().__init__(message)
        self.message = message
        self.resource = resource


def list_not_found(list_id: int) -> NotFoundError:
    return NotFoundError(f"List {list_id} not found", resource="list")


def todo_not_found(todo_id: int) -> NotFoundError:
    return NotFoundError(f"Todo {todo_id} not found", resource="todo")


def todo_not_in_list(todo_id: int, list_id: int) -> NotFoundError:
    """Used when a todo is addressed through a list it does not belong to."""
    return NotFoundError(f"Todo {todo_id} not found in list {list_id}", resource="todo")


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, NotFoundError)
    return JSONResponse(status_code=404, content={"detail": exc.message})
