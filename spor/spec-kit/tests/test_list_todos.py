"""Todos inside a list: creating them there, and reading back only that list's."""

from fastapi.testclient import TestClient


def make_list(client: TestClient, name: str = "Handleliste") -> int:
    return client.post("/lists", json={"name": name}).json()["id"]


def test_create_todo_starts_not_done_and_knows_its_list(client: TestClient) -> None:
    list_id = make_list(client)

    response = client.post(f"/lists/{list_id}/todos", json={"title": "Kjøpe melk"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Kjøpe melk"
    assert body["done"] is False
    assert body["list_id"] == list_id
    assert isinstance(body["id"], int)


def test_create_todo_accepts_an_explicit_done_status(client: TestClient) -> None:
    list_id = make_list(client)

    response = client.post(
        f"/lists/{list_id}/todos", json={"title": "Allerede gjort", "done": True}
    )

    assert response.status_code == 201
    assert response.json()["done"] is True


def test_list_todos_returns_that_list_only(client: TestClient) -> None:
    first = make_list(client, "Første")
    second = make_list(client, "Andre")
    client.post(f"/lists/{first}/todos", json={"title": "Melk"})
    client.post(f"/lists/{first}/todos", json={"title": "Brød"})
    client.post(f"/lists/{second}/todos", json={"title": "Noe annet"})

    response = client.get(f"/lists/{first}/todos")

    assert response.status_code == 200
    assert [todo["title"] for todo in response.json()] == ["Melk", "Brød"]


def test_empty_list_returns_empty_collection_not_a_miss(client: TestClient) -> None:
    """An existing list with no todos is a success, not a 404."""
    list_id = make_list(client)

    response = client.get(f"/lists/{list_id}/todos")

    assert response.status_code == 200
    assert response.json() == []


def test_todo_readable_through_its_own_list(client: TestClient) -> None:
    list_id = make_list(client)
    todo_id = client.post(f"/lists/{list_id}/todos", json={"title": "Melk"}).json()["id"]

    response = client.get(f"/lists/{list_id}/todos/{todo_id}")

    assert response.status_code == 200
    assert response.json()["id"] == todo_id
