"""Flytting av et gjøremål mellom lister (FR-011).

Dette er det eneste endepunktet der en 404 kan bety to forskjellige ting, og
derfor grunnen til at feilkonvolutten har et resource-felt.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def oppsett(client: TestClient, liste: dict):
    """En liste med ett gjøremål, og en tom liste å flytte til."""
    mal = client.post("/lists", json={"name": "Jobb"}).json()
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    return liste, mal, gjoremal


def test_flytter_gjoremalet(client: TestClient, oppsett) -> None:
    _, mal, gjoremal = oppsett

    svar = client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": mal["id"]})

    assert svar.status_code == 200
    assert svar.json() == {**gjoremal, "list_id": mal["id"]}


def test_flytting_bevarer_innholdet(client: TestClient, liste: dict) -> None:
    mal = client.post("/lists", json={"name": "Jobb"}).json()
    gjoremal = client.post(
        f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk", "done": True}
    ).json()

    flyttet = client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": mal["id"]}).json()

    assert flyttet["id"] == gjoremal["id"]
    assert flyttet["title"] == "Kjøpe melk"
    assert flyttet["done"] is True


def test_borte_fra_kildelisten_og_i_mallisten(client: TestClient, oppsett) -> None:
    kilde, mal, gjoremal = oppsett

    client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": mal["id"]})

    assert client.get(f"/lists/{kilde['id']}/todos").json() == []
    assert [g["id"] for g in client.get(f"/lists/{mal['id']}/todos").json()] == [gjoremal["id"]]


def test_flytting_til_egen_liste_er_lov(client: TestClient, oppsett) -> None:
    kilde, _, gjoremal = oppsett

    svar = client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": kilde["id"]})

    assert svar.status_code == 200
    assert svar.json() == gjoremal


def test_ukjent_gjoremal_gir_404_todo(client: TestClient, oppsett) -> None:
    _, mal, _ = oppsett

    svar = client.post("/todos/999/move", json={"list_id": mal["id"]})

    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "todo"


def test_ukjent_malliste_gir_404_list(client: TestClient, oppsett) -> None:
    _, _, gjoremal = oppsett

    svar = client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": 999})

    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "list"


def test_feilet_flytting_lar_gjoremalet_ligge(client: TestClient, oppsett) -> None:
    """FR-019: en feilet operasjon etterlater ingen endring."""
    kilde, _, gjoremal = oppsett

    client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": 999})

    assert client.get(f"/todos/{gjoremal['id']}").json() == gjoremal
    assert [g["id"] for g in client.get(f"/lists/{kilde['id']}/todos").json()] == [gjoremal["id"]]


def test_manglende_list_id_avvises(client: TestClient, oppsett) -> None:
    _, _, gjoremal = oppsett
    assert client.post(f"/todos/{gjoremal['id']}/move", json={}).status_code == 422
