"""Gjøremål: hvert endepunkt, flytting, cascade og at data overlever omstart."""

from __future__ import annotations

import pytest
from app.db import DB_ENV_VAR
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def gjoremal(client: TestClient, liste: dict) -> dict:
    return client.post(
        f"/lists/{liste['id']}/todos", json={"title": "Skriv rapport"}
    ).json()


def test_oppretter_gjoremal_i_liste(client: TestClient, liste: dict) -> None:
    response = client.post(f"/lists/{liste['id']}/todos", json={"title": "Skriv rapport"})

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "title": "Skriv rapport",
        "done": False,
        "list_id": liste["id"],
    }


def test_oppretter_i_liste_som_ikke_finnes(client: TestClient) -> None:
    response = client.post("/lists/404/todos", json={"title": "Skriv rapport"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}


def test_henter_gjoremal_i_liste(client: TestClient, liste: dict) -> None:
    assert client.get(f"/lists/{liste['id']}/todos").json() == []

    client.post(f"/lists/{liste['id']}/todos", json={"title": "Skriv rapport"})
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Les korrektur"})

    titler = [row["title"] for row in client.get(f"/lists/{liste['id']}/todos").json()]
    assert titler == ["Skriv rapport", "Les korrektur"]


def test_henter_gjoremal_i_liste_som_ikke_finnes(client: TestClient) -> None:
    """En tom liste og en liste som ikke eksisterer er ikke det samme."""
    response = client.get("/lists/404/todos")

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}


def test_henter_ett_gjoremal(client: TestClient, gjoremal: dict) -> None:
    response = client.get(f"/todos/{gjoremal['id']}")

    assert response.status_code == 200
    assert response.json() == gjoremal


def test_henter_gjoremal_som_ikke_finnes(client: TestClient) -> None:
    response = client.get("/todos/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Gjøremål 404 finnes ikke"}


def test_endrer_tittel_og_status(client: TestClient, gjoremal: dict) -> None:
    response = client.patch(
        f"/todos/{gjoremal['id']}", json={"title": "Skriv ferdig", "done": True}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Skriv ferdig"
    assert response.json()["done"] is True


def test_patch_rorer_ikke_utelatte_felt(client: TestClient, gjoremal: dict) -> None:
    response = client.patch(f"/todos/{gjoremal['id']}", json={"done": True})

    assert response.json()["title"] == gjoremal["title"]
    assert response.json()["done"] is True


def test_endrer_gjoremal_som_ikke_finnes(client: TestClient) -> None:
    response = client.patch("/todos/404", json={"done": True})

    assert response.status_code == 404
    assert response.json() == {"detail": "Gjøremål 404 finnes ikke"}


def test_flytter_gjoremal_til_annen_liste(client: TestClient, gjoremal: dict) -> None:
    annen = client.post("/lists", json={"name": "Hjemme"}).json()

    response = client.patch(f"/todos/{gjoremal['id']}", json={"list_id": annen["id"]})

    assert response.status_code == 200
    assert response.json()["list_id"] == annen["id"]
    assert client.get(f"/lists/{gjoremal['list_id']}/todos").json() == []
    assert len(client.get(f"/lists/{annen['id']}/todos").json()) == 1


def test_flytter_til_liste_som_ikke_finnes(client: TestClient, gjoremal: dict) -> None:
    response = client.patch(f"/todos/{gjoremal['id']}", json={"list_id": 404})

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}
    assert client.get(f"/todos/{gjoremal['id']}").json()["list_id"] == gjoremal["list_id"]


def test_sletter_gjoremal(client: TestClient, gjoremal: dict) -> None:
    response = client.delete(f"/todos/{gjoremal['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/todos/{gjoremal['id']}").status_code == 404


def test_sletter_gjoremal_som_ikke_finnes(client: TestClient) -> None:
    response = client.delete("/todos/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Gjøremål 404 finnes ikke"}


def test_sletting_av_liste_tar_gjoremalene_med_seg(
    client: TestClient, liste: dict, gjoremal: dict
) -> None:
    client.delete(f"/lists/{liste['id']}")

    assert client.get(f"/todos/{gjoremal['id']}").status_code == 404


def test_data_overlever_omstart(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DB_ENV_VAR, str(tmp_path / "omstart.db"))

    with TestClient(app) as forste:
        list_id = forste.post("/lists", json={"name": "Jobb"}).json()["id"]
        forste.post(f"/lists/{list_id}/todos", json={"title": "Skriv rapport"})

    with TestClient(app) as andre:
        response = andre.get(f"/lists/{list_id}/todos")

        assert response.status_code == 200
        assert [row["title"] for row in response.json()] == ["Skriv rapport"]
