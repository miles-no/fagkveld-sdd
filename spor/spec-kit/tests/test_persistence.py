"""Data has to survive the application going away and coming back."""

from pathlib import Path

from fastapi.testclient import TestClient
from todo.main import app


def test_data_survives_a_restart(client: TestClient, db_path: Path) -> None:
    list_id = client.post("/lists", json={"name": "Handleliste"}).json()["id"]
    todo = client.post(
        f"/lists/{list_id}/todos", json={"title": "Kjøpe melk", "done": True}
    ).json()

    # The first application is done with; a second one opens the same file the
    # way a restarted process would.
    with TestClient(app) as restarted:
        lists = restarted.get("/lists").json()
        todos = restarted.get(f"/lists/{list_id}/todos").json()

    assert db_path.exists()
    assert lists == [{"id": list_id, "name": "Handleliste"}]
    assert todos == [
        {"id": todo["id"], "title": "Kjøpe melk", "done": True, "list_id": list_id}
    ]


def test_schema_creation_is_idempotent(client: TestClient) -> None:
    """Starting again against a populated file must not wipe or fail on it."""
    client.post("/lists", json={"name": "Beholdes"})

    with TestClient(app) as restarted:
        assert len(restarted.get("/lists").json()) == 1

    with TestClient(app) as restarted_again:
        assert len(restarted_again.get("/lists").json()) == 1
