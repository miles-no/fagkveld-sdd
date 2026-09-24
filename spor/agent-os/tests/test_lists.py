"""Lister: hvert endepunkt både når listen finnes og når den ikke gjør det."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_oppretter_liste(client: TestClient) -> None:
    response = client.post("/lists", json={"name": "Jobb"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "name": "Jobb"}


def test_tomt_navn_avvises(client: TestClient) -> None:
    assert client.post("/lists", json={"name": ""}).status_code == 422


def test_henter_alle_lister(client: TestClient) -> None:
    assert client.get("/lists").json() == []

    client.post("/lists", json={"name": "Jobb"})
    client.post("/lists", json={"name": "Hjemme"})

    assert [row["name"] for row in client.get("/lists").json()] == ["Jobb", "Hjemme"]


def test_henter_en_liste(client: TestClient, liste: dict) -> None:
    response = client.get(f"/lists/{liste['id']}")

    assert response.status_code == 200
    assert response.json() == liste


def test_henter_liste_som_ikke_finnes(client: TestClient) -> None:
    response = client.get("/lists/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}


def test_endrer_navn(client: TestClient, liste: dict) -> None:
    response = client.patch(f"/lists/{liste['id']}", json={"name": "Arbeid"})

    assert response.status_code == 200
    assert response.json()["name"] == "Arbeid"


def test_tom_patch_lar_listen_sta(client: TestClient, liste: dict) -> None:
    assert client.patch(f"/lists/{liste['id']}", json={}).json() == liste


def test_navn_satt_til_null_avvises(client: TestClient, liste: dict) -> None:
    assert client.patch(f"/lists/{liste['id']}", json={"name": None}).status_code == 422


def test_endrer_liste_som_ikke_finnes(client: TestClient) -> None:
    response = client.patch("/lists/404", json={"name": "Arbeid"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}


def test_sletter_liste(client: TestClient, liste: dict) -> None:
    response = client.delete(f"/lists/{liste['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/lists/{liste['id']}").status_code == 404


def test_sletter_liste_som_ikke_finnes(client: TestClient) -> None:
    response = client.delete("/lists/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Liste 404 finnes ikke"}
