"""Shared fixtures."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A client backed by an empty database of its own."""
    monkeypatch.setattr(db, "DATABASE_PATH", tmp_path / "notes.db")
    with TestClient(app) as test_client:
        yield test_client
