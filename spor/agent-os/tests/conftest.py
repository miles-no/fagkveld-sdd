"""Fikstur som gir hver test sin egen database.

Databasestien leses fra miljøet ved hvert kall, så det holder å sette
variabelen før klienten startes. TestClient brukes som kontekstmanager,
slik at lifespan kjører og skjemaet blir opprettet.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from app.db import DB_ENV_VAR
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setenv(DB_ENV_VAR, str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def liste(client: TestClient) -> dict:
    """En ferdig opprettet liste, for testene som trenger noe å henge på."""
    return client.post("/lists", json={"name": "Jobb"}).json()
