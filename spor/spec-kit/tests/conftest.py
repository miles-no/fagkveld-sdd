"""Each test gets its own database file, so no test can see another's rows."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo.main import app


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "todo.db"
    monkeypatch.setenv("TODO_DB_PATH", str(path))
    return path


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    # Entering the context manager runs the lifespan, which creates the schema
    # in the file db_path just pointed TODO_DB_PATH at.
    with TestClient(app) as test_client:
        yield test_client
