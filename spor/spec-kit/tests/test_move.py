"""Moving a todo from one list to another."""

from fastapi.testclient import TestClient


def seed(client: TestClient) -> tuple[int, int, int]:
    """Two lists; the first holds one done todo."""
    source = client.post("/lists", json={"name": "Nå"}).json()["id"]
    target = client.post("/lists", json={"name": "Senere"}).json()["id"]
    todo_id = client.post(
        f"/lists/{source}/todos", json={"title": "Kjøpe melk", "done": True}
    ).json()["id"]
    return source, target, todo_id


def test_move_keeps_identity_title_and_status(client: TestClient) -> None:
    _, target, todo_id = seed(client)

    response = client.post(f"/todos/{todo_id}/move", json={"list_id": target})

    assert response.status_code == 200
    assert response.json() == {
        "id": todo_id,
        "title": "Kjøpe melk",
        "done": True,
        "list_id": target,
    }


def test_move_updates_both_lists(client: TestClient) -> None:
    source, target, todo_id = seed(client)

    client.post(f"/todos/{todo_id}/move", json={"list_id": target})

    assert client.get(f"/lists/{source}/todos").json() == []
    assert [t["id"] for t in client.get(f"/lists/{target}/todos").json()] == [todo_id]


def test_move_changes_which_list_can_read_the_todo(client: TestClient) -> None:
    source, target, todo_id = seed(client)

    client.post(f"/todos/{todo_id}/move", json={"list_id": target})

    assert client.get(f"/lists/{target}/todos/{todo_id}").status_code == 200
    assert client.get(f"/lists/{source}/todos/{todo_id}").status_code == 404


def test_move_to_the_same_list_is_a_no_op(client: TestClient) -> None:
    source, _, todo_id = seed(client)
    before = client.get(f"/todos/{todo_id}").json()

    response = client.post(f"/todos/{todo_id}/move", json={"list_id": source})

    assert response.status_code == 200
    assert response.json() == before


def test_move_of_a_missing_todo_reports_the_todo(client: TestClient) -> None:
    _, target, _ = seed(client)

    response = client.post("/todos/999/move", json={"list_id": target})

    assert response.status_code == 404
    assert response.json()["detail"] == "Todo 999 not found"


def test_moved_todo_dies_with_its_new_list(client: TestClient) -> None:
    source, target, todo_id = seed(client)
    client.post(f"/todos/{todo_id}/move", json={"list_id": target})

    client.delete(f"/lists/{target}")

    assert client.get(f"/todos/{todo_id}").status_code == 404
    assert client.get(f"/lists/{source}").status_code == 200
