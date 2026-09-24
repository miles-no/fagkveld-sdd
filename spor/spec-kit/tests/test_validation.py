"""Bad input is rejected as bad input -- 422, distinct from a 404 miss."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def list_id(client: TestClient) -> int:
    return client.post("/lists", json={"name": "Handleliste"}).json()["id"]


@pytest.mark.parametrize("name", ["", "   ", "\t\n"])
def test_empty_list_name_is_rejected(client: TestClient, name: str) -> None:
    assert client.post("/lists", json={"name": name}).status_code == 422


@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_empty_todo_title_is_rejected(
    client: TestClient, list_id: int, title: str
) -> None:
    assert client.post(f"/lists/{list_id}/todos", json={"title": title}).status_code == 422


def test_empty_name_on_rename_is_rejected(client: TestClient, list_id: int) -> None:
    assert client.patch(f"/lists/{list_id}", json={"name": "  "}).status_code == 422


def test_missing_required_field_is_rejected(client: TestClient) -> None:
    assert client.post("/lists", json={}).status_code == 422


def test_empty_update_body_is_rejected(client: TestClient, list_id: int) -> None:
    """An update that changes nothing is a mistake, not a no-op."""
    todo_id = client.post(f"/lists/{list_id}/todos", json={"title": "Melk"}).json()["id"]

    assert client.patch(f"/todos/{todo_id}", json={}).status_code == 422
    assert client.patch(f"/lists/{list_id}", json={}).status_code == 422


def test_non_integer_identifier_is_rejected(client: TestClient) -> None:
    """A malformed id is bad input, not a missing resource."""
    assert client.get("/lists/ikke-et-tall").status_code == 422
    assert client.get("/todos/ikke-et-tall").status_code == 422


def test_invalid_input_is_not_confused_with_not_found(
    client: TestClient, list_id: int
) -> None:
    assert client.post("/lists", json={"name": ""}).status_code == 422
    assert client.get("/lists/999").status_code == 404


def test_titles_keep_their_characters_but_lose_surrounding_space(
    client: TestClient, list_id: int
) -> None:
    response = client.post(f"/lists/{list_id}/todos", json={"title": "  Kjøpe blåbær  "})

    assert response.status_code == 201
    assert response.json()["title"] == "Kjøpe blåbær"


def test_a_list_name_may_repeat(client: TestClient) -> None:
    """Names are labels, not identifiers."""
    first = client.post("/lists", json={"name": "Samme"})
    second = client.post("/lists", json={"name": "Samme"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]
