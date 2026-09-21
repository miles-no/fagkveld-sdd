"""Notes API."""

from fastapi.testclient import TestClient

PAYLOAD = {"title": "Shopping", "body": "Milk and bread"}


def test_list_is_empty_initially(client: TestClient) -> None:
    response = client.get("/notes")
    assert response.status_code == 200
    assert response.json() == []


def test_create_returns_the_stored_note(client: TestClient) -> None:
    response = client.post("/notes", json=PAYLOAD)
    assert response.status_code == 201
    note = response.json()
    assert note["id"] > 0
    assert note["title"] == PAYLOAD["title"]
    assert note["body"] == PAYLOAD["body"]
    assert note["created_at"]


def test_created_note_can_be_read_back(client: TestClient) -> None:
    note_id = client.post("/notes", json=PAYLOAD).json()["id"]

    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["title"] == PAYLOAD["title"]

    listing = client.get("/notes")
    assert [n["id"] for n in listing.json()] == [note_id]


def test_replace_overwrites_both_fields(client: TestClient) -> None:
    note_id = client.post("/notes", json=PAYLOAD).json()["id"]

    response = client.put(f"/notes/{note_id}", json={"title": "Errands", "body": "Eggs"})
    assert response.status_code == 200
    assert response.json() == {
        **response.json(),
        "id": note_id,
        "title": "Errands",
        "body": "Eggs",
    }
    assert client.get(f"/notes/{note_id}").json()["title"] == "Errands"


def test_delete_removes_the_note(client: TestClient) -> None:
    note_id = client.post("/notes", json=PAYLOAD).json()["id"]

    assert client.delete(f"/notes/{note_id}").status_code == 204
    assert client.get(f"/notes/{note_id}").status_code == 404
    assert client.get("/notes").json() == []


def test_get_unknown_id_returns_404(client: TestClient) -> None:
    response = client.get("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_replace_unknown_id_returns_404(client: TestClient) -> None:
    response = client.put("/notes/999", json=PAYLOAD)
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"


def test_delete_unknown_id_returns_404(client: TestClient) -> None:
    response = client.delete("/notes/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"
