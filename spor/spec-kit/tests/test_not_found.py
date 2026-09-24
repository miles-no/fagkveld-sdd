"""Asking for something that is not there is a normal answer, not a breakdown.

Every route in the contract's route table that resolves an identifier appears
here, aimed at something that does not exist.
"""

from fastapi.testclient import TestClient

MISSING = 999


def seed(client: TestClient) -> tuple[int, int]:
    """A list holding one todo."""
    list_id = client.post("/lists", json={"name": "Handleliste"}).json()["id"]
    todo_id = client.post(f"/lists/{list_id}/todos", json={"title": "Melk"}).json()["id"]
    return list_id, todo_id


def test_missing_list_routes_return_404_naming_the_list(client: TestClient) -> None:
    calls = [
        client.get(f"/lists/{MISSING}"),
        client.patch(f"/lists/{MISSING}", json={"name": "Nytt navn"}),
        client.delete(f"/lists/{MISSING}"),
        client.get(f"/lists/{MISSING}/todos"),
        client.post(f"/lists/{MISSING}/todos", json={"title": "Melk"}),
    ]

    for response in calls:
        assert response.status_code == 404, response.request.url
        assert response.json()["detail"] == f"List {MISSING} not found"


def test_missing_todo_routes_return_404_naming_the_todo(client: TestClient) -> None:
    calls = [
        client.get(f"/todos/{MISSING}"),
        client.patch(f"/todos/{MISSING}", json={"done": True}),
        client.delete(f"/todos/{MISSING}"),
    ]

    for response in calls:
        assert response.status_code == 404, response.request.url
        assert response.json()["detail"] == f"Todo {MISSING} not found"


def test_todo_under_the_wrong_list_is_not_found(client: TestClient) -> None:
    list_id, todo_id = seed(client)
    other_list = client.post("/lists", json={"name": "Andre"}).json()["id"]

    response = client.get(f"/lists/{other_list}/todos/{todo_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Todo {todo_id} not found in list {other_list}"
    # ...while the same todo is readable through the list it is actually in.
    assert client.get(f"/lists/{list_id}/todos/{todo_id}").status_code == 200


def test_move_to_a_missing_list_reports_the_destination(client: TestClient) -> None:
    """The todo was found; the destination was not, so the destination is named."""
    _, todo_id = seed(client)

    response = client.post(f"/todos/{todo_id}/move", json={"list_id": MISSING})

    assert response.status_code == 404
    assert response.json()["detail"] == f"List {MISSING} not found"


def test_nothing_is_written_when_the_list_does_not_exist(client: TestClient) -> None:
    list_id, _ = seed(client)

    client.post(f"/lists/{MISSING}/todos", json={"title": "Skal ikke lagres"})

    assert len(client.get(f"/lists/{list_id}/todos").json()) == 1


def test_a_failed_move_leaves_the_todo_where_it_was(client: TestClient) -> None:
    list_id, todo_id = seed(client)

    client.post(f"/todos/{todo_id}/move", json={"list_id": MISSING})

    assert client.get(f"/todos/{todo_id}").json()["list_id"] == list_id
    assert len(client.get(f"/lists/{list_id}/todos").json()) == 1


def test_the_service_keeps_serving_after_a_miss(client: TestClient) -> None:
    list_id, _ = seed(client)

    assert client.get(f"/lists/{MISSING}").status_code == 404
    assert client.get(f"/todos/{MISSING}").status_code == 404
    assert client.get(f"/lists/{list_id}").status_code == 200


def test_a_miss_is_never_a_server_error(client: TestClient) -> None:
    """The point of the requirement: 404, not 500, and no stack trace leaking."""
    responses = [
        client.get(f"/lists/{MISSING}"),
        client.get(f"/todos/{MISSING}"),
        client.get(f"/lists/{MISSING}/todos"),
    ]

    for response in responses:
        assert response.status_code < 500
        assert set(response.json()) == {"detail"}
