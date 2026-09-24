"""Gjøremål: oppretting i liste og henting per liste (FR-006, FR-010),
og senere hente/endre/slette ett gjøremål (FR-007 til FR-009).
"""

from fastapi.testclient import TestClient

# --- FR-006: opprette i en liste ----------------------------------------------


def test_oppretter_gjoremal(client: TestClient, liste: dict) -> None:
    svar = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})
    assert svar.status_code == 201
    assert svar.json() == {
        "id": 1,
        "title": "Kjøpe melk",
        "done": False,
        "list_id": liste["id"],
    }


def test_status_kan_settes_ved_oppretting(client: TestClient, liste: dict) -> None:
    svar = client.post(
        f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk", "done": True}
    )
    assert svar.json()["done"] is True


def test_tom_tittel_avvises(client: TestClient, liste: dict) -> None:
    svar = client.post(f"/lists/{liste['id']}/todos", json={"title": "   "})
    assert svar.status_code == 422


def test_oppretting_i_ukjent_liste_gir_404(client: TestClient) -> None:
    """404, ikke en 500 fra fremmednøkkelen."""
    svar = client.post("/lists/999/todos", json={"title": "Kjøpe melk"})
    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "list"


# --- FR-010: gjøremålene i en liste -------------------------------------------


def test_henter_gjoremalene_i_listen(client: TestClient, liste: dict) -> None:
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe brød"})

    svar = client.get(f"/lists/{liste['id']}/todos")

    assert svar.status_code == 200
    assert [g["title"] for g in svar.json()] == ["Kjøpe melk", "Kjøpe brød"]


def test_andre_listers_gjoremal_blandes_ikke_inn(client: TestClient, liste: dict) -> None:
    annen = client.post("/lists", json={"name": "Jobb"}).json()
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})
    client.post(f"/lists/{annen['id']}/todos", json={"title": "Sende faktura"})

    svar = client.get(f"/lists/{liste['id']}/todos")

    assert [g["title"] for g in svar.json()] == ["Kjøpe melk"]


def test_tom_liste_gir_tom_samling(client: TestClient, liste: dict) -> None:
    svar = client.get(f"/lists/{liste['id']}/todos")
    assert svar.status_code == 200
    assert svar.json() == []


def test_ukjent_liste_gir_404_ikke_tom_samling(client: TestClient) -> None:
    """En tom liste og en liste som ikke finnes er to ulike situasjoner."""
    svar = client.get("/lists/999/todos")
    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "list"


# --- FR-007: hente ett gjøremål -----------------------------------------------


def test_henter_ett_gjoremal(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    svar = client.get(f"/todos/{opprettet['id']}")
    assert svar.status_code == 200
    assert svar.json() == opprettet


def test_ukjent_gjoremal_gir_404(client: TestClient) -> None:
    svar = client.get("/todos/999")
    assert svar.status_code == 404
    assert svar.json()["error"]["resource"] == "todo"


# --- FR-008: endre delvis -----------------------------------------------------


def test_setter_status_uten_a_miste_tittelen(client: TestClient, liste: dict) -> None:
    """Kjernen i FR-008: sender du bare done, skal tittelen bli stående."""
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    svar = client.patch(f"/todos/{opprettet['id']}", json={"done": True})

    assert svar.status_code == 200
    assert svar.json() == {**opprettet, "done": True}


def test_endrer_tittel_uten_a_miste_status(client: TestClient, liste: dict) -> None:
    opprettet = client.post(
        f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk", "done": True}
    ).json()

    svar = client.patch(f"/todos/{opprettet['id']}", json={"title": "Kjøpe havremelk"})

    assert svar.json() == {**opprettet, "title": "Kjøpe havremelk"}


def test_endrer_begge_samtidig(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    svar = client.patch(f"/todos/{opprettet['id']}", json={"title": "Kjøpe brød", "done": True})
    assert svar.json() == {**opprettet, "title": "Kjøpe brød", "done": True}


def test_status_kan_settes_tilbake_til_ikke_gjort(client: TestClient, liste: dict) -> None:
    opprettet = client.post(
        f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk", "done": True}
    ).json()
    svar = client.patch(f"/todos/{opprettet['id']}", json={"done": False})
    assert svar.json()["done"] is False


def test_tom_kropp_lar_gjoremalet_sta(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    svar = client.patch(f"/todos/{opprettet['id']}", json={})
    assert svar.status_code == 200
    assert svar.json() == opprettet


def test_patch_ukjent_gjoremal_gir_404(client: TestClient) -> None:
    assert client.patch("/todos/999", json={"done": True}).status_code == 404


def test_patch_tom_tittel_avvises(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    assert client.patch(f"/todos/{opprettet['id']}", json={"title": " "}).status_code == 422


def test_patch_kan_ikke_flytte_gjoremalet(client: TestClient, liste: dict) -> None:
    """Flytting er et eget endepunkt; list_id hører ikke hjemme i PATCH."""
    annen = client.post("/lists", json={"name": "Jobb"}).json()
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    svar = client.patch(f"/todos/{opprettet['id']}", json={"list_id": annen["id"]})

    assert svar.status_code == 422


# --- FR-009: slette -----------------------------------------------------------


def test_sletter_gjoremal(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    assert client.delete(f"/todos/{opprettet['id']}").status_code == 204

    assert client.get(f"/todos/{opprettet['id']}").status_code == 404


def test_sletting_rorer_ikke_listen(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    client.delete(f"/todos/{opprettet['id']}")
    assert client.get(f"/lists/{liste['id']}/todos").json() == []


def test_sletting_av_gjoremal_to_ganger_gir_404(client: TestClient, liste: dict) -> None:
    opprettet = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    client.delete(f"/todos/{opprettet['id']}")
    assert client.delete(f"/todos/{opprettet['id']}").status_code == 404
