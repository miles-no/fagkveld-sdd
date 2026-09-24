"""Fravær og feil er normale svar (FR-012 til FR-016).

Kravets kjerne: et oppslag mot noe som ikke finnes er en normal situasjon, og
alle feilsvar har samme form uansett hvor de kommer fra.
"""

import pytest
from fastapi.testclient import TestClient

KONVOLUTT_FELT = {"code", "resource", "message", "details"}


def _feil(svar) -> dict:
    kropp = svar.json()
    assert set(kropp) == {"error"}, f"uventet kroppsform: {kropp}"
    assert set(kropp["error"]) == KONVOLUTT_FELT
    return kropp["error"]


# --- FR-016: én form, uansett opphav ------------------------------------------


def test_404_bruker_konvolutten(client: TestClient) -> None:
    feil = _feil(client.get("/lists/999"))
    assert feil["code"] == "not_found"
    assert feil["resource"] == "list"
    assert feil["message"]
    assert feil["details"] == []


def test_422_bruker_samme_konvolutt(client: TestClient) -> None:
    feil = _feil(client.post("/lists", json={"name": ""}))
    assert feil["code"] == "invalid_request"
    assert feil["resource"] is None
    assert feil["details"], "valideringsfeil skal si hva som er galt"


def test_ukjent_rute_bruker_samme_konvolutt(client: TestClient) -> None:
    """Rammeverkets egen 404. Registreres håndtereren på fastapi.HTTPException
    i stedet for Starlettes, svarer denne {"detail": "Not Found"}.
    """
    svar = client.get("/finnes-ikke")
    assert svar.status_code == 404
    assert _feil(svar)["code"] == "not_found"


def test_feil_metode_bruker_samme_konvolutt(client: TestClient) -> None:
    svar = client.post("/todos/1")
    assert svar.status_code == 405
    _feil(svar)


def test_alle_feilsvar_har_identisk_form(client: TestClient, liste: dict) -> None:
    svar = [
        client.get("/lists/999"),
        client.get("/todos/999"),
        client.post("/lists", json={"name": ""}),
        client.get("/lists/abc"),
        client.get("/finnes-ikke"),
        client.post("/todos/1"),
    ]
    for s in svar:
        _feil(s)


# --- FR-013: resource skiller list fra todo -----------------------------------


def test_resource_skiller_liste_fra_gjoremal(client: TestClient, liste: dict) -> None:
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    ukjent_gjoremal = client.post("/todos/999/move", json={"list_id": liste["id"]})
    ukjent_liste = client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": 999})

    assert _feil(ukjent_gjoremal)["resource"] == "todo"
    assert _feil(ukjent_liste)["resource"] == "list"


# --- FR-014: ugyldig inndata --------------------------------------------------


@pytest.mark.parametrize("sti", ["/lists/abc", "/todos/abc", "/lists/1.5/todos"])
def test_id_paa_feil_form_gir_422_ikke_404(client: TestClient, sti: str) -> None:
    """En id som ikke er et heltall er ugyldig inndata, ikke noe som mangler."""
    assert client.get(sti).status_code == 422


def test_ukjent_felt_avvises(client: TestClient) -> None:
    assert client.post("/lists", json={"name": "Handel", "farge": "rød"}).status_code == 422


def test_feilstavet_felt_avvises_ikke_ignoreres(client: TestClient, liste: dict) -> None:
    svar = client.post(f"/lists/{liste['id']}/todos", json={"titel": "Kjøpe melk"})
    assert svar.status_code == 422


def test_eksplisitt_null_avvises(client: TestClient, liste: dict) -> None:
    """NOT NULL i skjemaet; uten denne sperren ville det blitt en 500."""
    assert client.patch(f"/lists/{liste['id']}", json={"name": None}).status_code == 422


def test_for_langt_navn_avvises(client: TestClient) -> None:
    assert client.post("/lists", json={"name": "x" * 201}).status_code == 422


def test_for_lang_tittel_avvises(client: TestClient, liste: dict) -> None:
    svar = client.post(f"/lists/{liste['id']}/todos", json={"title": "x" * 501})
    assert svar.status_code == 422


def test_feil_type_avvises(client: TestClient, liste: dict) -> None:
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    assert client.patch(f"/todos/{gjoremal['id']}", json={"done": "kanskje"}).status_code == 422


# --- FR-015: ingenting svarer 5xx ---------------------------------------------


def test_ingen_vei_gir_serverfeil(client: TestClient) -> None:
    """Sveip over alle 11 endepunkter med ukjente og ugyldige id-er."""
    kall = [
        ("GET", "/lists", None),
        ("POST", "/lists", {"name": ""}),
        ("GET", "/lists/999", None),
        ("GET", "/lists/abc", None),
        ("PATCH", "/lists/999", {"name": "X"}),
        ("PATCH", "/lists/abc", {"name": "X"}),
        ("DELETE", "/lists/999", None),
        ("DELETE", "/lists/abc", None),
        ("GET", "/lists/999/todos", None),
        ("GET", "/lists/abc/todos", None),
        ("POST", "/lists/999/todos", {"title": "X"}),
        ("POST", "/lists/1/todos", {"title": ""}),
        ("GET", "/todos/999", None),
        ("GET", "/todos/abc", None),
        ("PATCH", "/todos/999", {"done": True}),
        ("PATCH", "/todos/abc", {"done": True}),
        ("DELETE", "/todos/999", None),
        ("DELETE", "/todos/abc", None),
        ("POST", "/todos/999/move", {"list_id": 1}),
        ("POST", "/todos/1/move", {"list_id": 999}),
        ("POST", "/todos/abc/move", {"list_id": 1}),
        ("POST", "/todos/1/move", {}),
        ("GET", "/finnes-ikke", None),
        ("POST", "/todos/1", None),
    ]
    for metode, sti, kropp in kall:
        svar = client.request(metode, sti, json=kropp)
        assert svar.status_code < 500, f"{metode} {sti} ga {svar.status_code}"


def test_ugyldig_json_gir_ikke_serverfeil(client: TestClient) -> None:
    svar = client.post(
        "/lists", content=b"{ikke gyldig json", headers={"content-type": "application/json"}
    )
    assert svar.status_code < 500


# --- FR-012/SC-007: klassifiserbart uten å lese meldingen ---------------------


def test_klienten_trenger_ikke_lese_meldingsteksten(client: TestClient) -> None:
    koder = {
        client.get("/lists/999").json()["error"]["code"],
        client.post("/lists", json={"name": ""}).json()["error"]["code"],
    }
    assert koder == {"not_found", "invalid_request"}
