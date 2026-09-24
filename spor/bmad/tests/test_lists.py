from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo_api.main import create_app


def test_create_list_returns_201_with_id_and_name(client: TestClient) -> None:
    response = client.post("/lists", json={"name": "Groceries"})

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert body == {"id": body["id"], "name": "Groceries"}


def test_get_list_by_id(client: TestClient) -> None:
    created = client.post("/lists", json={"name": "Groceries"}).json()

    response = client.get(f"/lists/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_lists_returns_all_ordered_by_id(client: TestClient) -> None:
    first = client.post("/lists", json={"name": "A"}).json()
    second = client.post("/lists", json={"name": "B"}).json()

    response = client.get("/lists")

    assert response.status_code == 200
    assert response.json() == [first, second]


def test_get_lists_when_empty_returns_empty_array(client: TestClient) -> None:
    response = client.get("/lists")

    assert response.status_code == 200
    assert response.json() == []


def test_get_missing_list_returns_404(client: TestClient) -> None:
    response = client.get("/lists/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "List 999 not found"}


@pytest.mark.parametrize("body", [{"name": ""}, {"name": "   "}, {}])
def test_create_list_with_invalid_name_returns_422(client: TestClient, body: dict) -> None:
    response = client.post("/lists", json=body)

    assert response.status_code == 422
    assert client.get("/lists").json() == []


def test_create_list_strips_surrounding_whitespace(client: TestClient) -> None:
    response = client.post("/lists", json={"name": "  Groceries  "})

    assert response.status_code == 201
    assert response.json()["name"] == "Groceries"


def test_get_list_with_non_integer_id_returns_422(client: TestClient) -> None:
    response = client.get("/lists/abc")

    assert response.status_code == 422


def test_lists_survive_restart(db_path: Path) -> None:
    with TestClient(create_app(db_path)) as first_run:
        created = first_run.post("/lists", json={"name": "Groceries"}).json()

    with TestClient(create_app(db_path)) as second_run:
        response = second_run.get(f"/lists/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created
