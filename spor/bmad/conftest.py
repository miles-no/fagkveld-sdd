from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo_api.main import create_app


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(db_path)) as test_client:
        yield test_client
