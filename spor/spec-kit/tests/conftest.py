from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo_api.main import create_app


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Egen databasefil per test.

    En :memory:-base ville ikke vist om data faktisk overlever, og ville dessuten
    gitt hver forespørsel sin egen tomme base, siden tilkoblingen er per
    forespørsel.
    """
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(db_path)) as client:
        yield client


@pytest.fixture
def liste(client: TestClient):
    """En ferdig opprettet liste, som de fleste testene trenger."""
    return client.post("/lists", json={"name": "Handel"}).json()
