"""Lister: oppretting (FR-001) og forvaltning (FR-002 til FR-005)."""

import pytest
from fastapi.testclient import TestClient

# --- FR-001: opprette ---------------------------------------------------------


def test_oppretter_liste(client: TestClient) -> None:
    svar = client.post("/lists", json={"name": "Handel"})
    assert svar.status_code == 201
    assert svar.json() == {"id": 1, "name": "Handel"}


def test_navnet_trimmes(client: TestClient) -> None:
    svar = client.post("/lists", json={"name": "  Handel  "})
    assert svar.json()["name"] == "Handel"


def test_to_lister_kan_hete_det_samme(client: TestClient) -> None:
    en = client.post("/lists", json={"name": "Handel"}).json()
    to = client.post("/lists", json={"name": "Handel"}).json()
    assert en["id"] != to["id"]


@pytest.mark.parametrize("navn", ["", "   ", "\t\n"])
def test_tomt_navn_avvises(client: TestClient, navn: str) -> None:
    assert client.post("/lists", json={"name": navn}).status_code == 422


def test_manglende_navn_avvises(client: TestClient) -> None:
    assert client.post("/lists", json={}).status_code == 422


# --- FR-002: hente alle -------------------------------------------------------


def test_henter_alle_lister_sortert(client: TestClient) -> None:
    client.post("/lists", json={"name": "Handel"})
    client.post("/lists", json={"name": "Jobb"})
    svar = client.get("/lists")
    assert svar.status_code == 200
    assert [liste["name"] for liste in svar.json()] == ["Handel", "Jobb"]


def test_ingen_lister_gir_tom_samling(client: TestClient) -> None:
    svar = client.get("/lists")
    assert svar.status_code == 200
    assert svar.json() == []


# --- FR-003: hente én ---------------------------------------------------------


def test_henter_en_liste(client: TestClient, liste: dict) -> None:
    svar = client.get(f"/lists/{liste['id']}")
    assert svar.status_code == 200
    assert svar.json() == liste


def test_ukjent_liste_gir_404(client: TestClient) -> None:
    svar = client.get("/lists/999")
    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "list"


# --- FR-004: endre navn -------------------------------------------------------


def test_endrer_navn(client: TestClient, liste: dict) -> None:
    svar = client.patch(f"/lists/{liste['id']}", json={"name": "Matbutikk"})
    assert svar.status_code == 200
    assert svar.json() == {"id": liste["id"], "name": "Matbutikk"}
    assert client.get(f"/lists/{liste['id']}").json()["name"] == "Matbutikk"


def test_navneendring_rorer_ikke_gjoremalene(client: TestClient, liste: dict) -> None:
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})
    client.patch(f"/lists/{liste['id']}", json={"name": "Matbutikk"})
    gjoremal = client.get(f"/lists/{liste['id']}/todos").json()
    assert [g["title"] for g in gjoremal] == ["Kjøpe melk"]


def test_tom_kropp_lar_listen_sta(client: TestClient, liste: dict) -> None:
    svar = client.patch(f"/lists/{liste['id']}", json={})
    assert svar.status_code == 200
    assert svar.json() == liste


def test_patch_ukjent_liste_gir_404(client: TestClient) -> None:
    assert client.patch("/lists/999", json={"name": "X"}).status_code == 404


def test_patch_tomt_navn_avvises(client: TestClient, liste: dict) -> None:
    assert client.patch(f"/lists/{liste['id']}", json={"name": "  "}).status_code == 422


# --- FR-005: slette, med cascade ----------------------------------------------


def test_sletter_liste(client: TestClient, liste: dict) -> None:
    assert client.delete(f"/lists/{liste['id']}").status_code == 204
    assert client.get(f"/lists/{liste['id']}").status_code == 404


def test_sletting_to_ganger_gir_404(client: TestClient, liste: dict) -> None:
    client.delete(f"/lists/{liste['id']}")
    assert client.delete(f"/lists/{liste['id']}").status_code == 404


def test_sletting_tar_gjoremalene_med(client: TestClient, liste: dict) -> None:
    """INV-2. Virker ikke dette, er PRAGMA foreign_keys som regel glemt."""
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    client.delete(f"/lists/{liste['id']}")

    assert client.get(f"/todos/{gjoremal['id']}").status_code == 404


def test_sletting_rorer_ikke_andre_listers_gjoremal(client: TestClient, liste: dict) -> None:
    annen = client.post("/lists", json={"name": "Jobb"}).json()
    beholdes = client.post(f"/lists/{annen['id']}/todos", json={"title": "Sende faktura"}).json()
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})

    client.delete(f"/lists/{liste['id']}")

    assert client.get(f"/todos/{beholdes['id']}").status_code == 200
