"""Todos over time: completing them, correcting them, removing them."""

from fastapi.testclient import TestClient


def seed(client: TestClient) -> tuple[int, int]:
    list_id = client.post("/lists", json={"name": "Handleliste"}).json()["id"]
    todo_id = client.post(f"/lists/{list_id}/todos", json={"title": "Melk"}).json()["id"]
    return list_id, todo_id


def test_get_todo_directly(client: TestClient) -> None:
    list_id, todo_id = seed(client)

    response = client.get(f"/todos/{todo_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": todo_id,
        "title": "Melk",
        "done": False,
        "list_id": list_id,
    }


def test_mark_done_and_undone(client: TestClient) -> None:
    _, todo_id = seed(client)

    done = client.patch(f"/todos/{todo_id}", json={"done": True})
    assert done.status_code == 200
    assert done.json()["done"] is True
    assert client.get(f"/todos/{todo_id}").json()["done"] is True

    undone = client.patch(f"/todos/{todo_id}", json={"done": False})
    assert undone.json()["done"] is False
    assert client.get(f"/todos/{todo_id}").json()["done"] is False


def test_changing_only_the_title_leaves_the_rest_alone(client: TestClient) -> None:
    list_id, todo_id = seed(client)
    client.patch(f"/todos/{todo_id}", json={"done": True})

    response = client.patch(f"/todos/{todo_id}", json={"title": "Havremelk"})

    assert response.json() == {
        "id": todo_id,
        "title": "Havremelk",
        "done": True,
        "list_id": list_id,
    }


def test_changing_only_the_status_leaves_the_title_alone(client: TestClient) -> None:
    _, todo_id = seed(client)

    response = client.patch(f"/todos/{todo_id}", json={"done": True})

    assert response.json()["title"] == "Melk"


def test_changing_both_fields_at_once(client: TestClient) -> None:
    _, todo_id = seed(client)

    response = client.patch(f"/todos/{todo_id}", json={"title": "Brød", "done": True})

    assert response.json()["title"] == "Brød"
    assert response.json()["done"] is True


def test_delete_todo_removes_it_from_its_list(client: TestClient) -> None:
    list_id, todo_id = seed(client)

    response = client.delete(f"/todos/{todo_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/todos/{todo_id}").status_code == 404
    assert client.get(f"/lists/{list_id}/todos").json() == []


def test_deleting_a_todo_leaves_the_list_standing(client: TestClient) -> None:
    list_id, todo_id = seed(client)

    client.delete(f"/todos/{todo_id}")

    assert client.get(f"/lists/{list_id}").status_code == 200
