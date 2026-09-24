"""Lists: create, read, rename, delete."""

from fastapi.testclient import TestClient


def test_create_list_returns_id_and_name(client: TestClient) -> None:
    response = client.post("/lists", json={"name": "Handleliste"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Handleliste"
    assert isinstance(body["id"], int)


def test_get_list_returns_the_created_list(client: TestClient) -> None:
    list_id = client.post("/lists", json={"name": "Handleliste"}).json()["id"]

    response = client.get(f"/lists/{list_id}")

    assert response.status_code == 200
    assert response.json() == {"id": list_id, "name": "Handleliste"}


def test_get_lists_returns_all_in_creation_order(client: TestClient) -> None:
    for name in ("Først", "Så", "Til slutt"):
        client.post("/lists", json={"name": name})

    response = client.get("/lists")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Først", "Så", "Til slutt"]


def test_get_lists_is_empty_when_nothing_created(client: TestClient) -> None:
    response = client.get("/lists")

    assert response.status_code == 200
    assert response.json() == []


def test_rename_list_keeps_id_and_todos(client: TestClient) -> None:
    list_id = client.post("/lists", json={"name": "Gammelt navn"}).json()["id"]
    client.post(f"/lists/{list_id}/todos", json={"title": "Melk"})

    response = client.patch(f"/lists/{list_id}", json={"name": "Nytt navn"})

    assert response.status_code == 200
    assert response.json() == {"id": list_id, "name": "Nytt navn"}
    assert [t["title"] for t in client.get(f"/lists/{list_id}/todos").json()] == ["Melk"]


def test_delete_list_takes_its_todos_with_it(client: TestClient) -> None:
    """The assertion that proves foreign keys are actually enforced."""
    list_id = client.post("/lists", json={"name": "Forsvinner"}).json()["id"]
    first = client.post(f"/lists/{list_id}/todos", json={"title": "Melk"}).json()["id"]
    second = client.post(f"/lists/{list_id}/todos", json={"title": "Brød"}).json()["id"]

    response = client.delete(f"/lists/{list_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/lists/{list_id}").status_code == 404
    assert client.get(f"/todos/{first}").status_code == 404
    assert client.get(f"/todos/{second}").status_code == 404


def test_deleting_one_list_leaves_another_alone(client: TestClient) -> None:
    doomed = client.post("/lists", json={"name": "Forsvinner"}).json()["id"]
    kept = client.post("/lists", json={"name": "Beholdes"}).json()["id"]
    kept_todo = client.post(f"/lists/{kept}/todos", json={"title": "Melk"}).json()["id"]

    client.delete(f"/lists/{doomed}")

    assert client.get(f"/lists/{kept}").status_code == 200
    assert client.get(f"/todos/{kept_todo}").status_code == 200
