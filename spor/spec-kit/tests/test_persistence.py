"""Varighet og integritet (FR-017 til FR-019)."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from todo_api.db import connect
from todo_api.main import create_app


def _foreldrelose(db_path: Path) -> int:
    """Gjøremål som peker på en liste som ikke finnes."""
    conn = connect(db_path)
    try:
        return conn.execute(
            "SELECT count(*) FROM todos"
            " WHERE list_id NOT IN (SELECT id FROM lists)"
        ).fetchone()[0]
    finally:
        conn.close()


# --- FR-017: data overlever omstart -------------------------------------------


def test_data_overlever_omstart(db_path: Path) -> None:
    """To apper etter hverandre mot samme fil skal se de samme dataene."""
    with TestClient(create_app(db_path)) as først:
        liste = først.post("/lists", json={"name": "Handel"}).json()
        gjoremal = først.post(
            f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk", "done": True}
        ).json()

    with TestClient(create_app(db_path)) as etterpå:
        assert etterpå.get("/lists").json() == [liste]
        assert etterpå.get(f"/todos/{gjoremal['id']}").json() == gjoremal


def test_id_er_uendret_etter_omstart(db_path: Path) -> None:
    with TestClient(create_app(db_path)) as først:
        ider = [først.post("/lists", json={"name": f"L{n}"}).json()["id"] for n in range(3)]

    with TestClient(create_app(db_path)) as etterpå:
        assert [liste["id"] for liste in etterpå.get("/lists").json()] == ider


def test_sletting_overlever_ogsaa(db_path: Path) -> None:
    with TestClient(create_app(db_path)) as først:
        liste = først.post("/lists", json={"name": "Handel"}).json()
        først.delete(f"/lists/{liste['id']}")

    with TestClient(create_app(db_path)) as etterpå:
        assert etterpå.get("/lists").json() == []


def test_tom_database_fungerer(db_path: Path) -> None:
    """Skjemaet opprettes idempotent — tom fil og eksisterende fil er begge ok."""
    assert not db_path.exists()
    with TestClient(create_app(db_path)) as client:
        assert client.get("/lists").json() == []
    assert db_path.exists()


# --- FR-018: ingen foreldreløse gjøremål --------------------------------------


def test_oppretting_kan_ikke_lage_foreldrelost_gjoremal(
    client: TestClient, db_path: Path
) -> None:
    client.post("/lists/999/todos", json={"title": "Kjøpe melk"})
    assert _foreldrelose(db_path) == 0


def test_flytting_kan_ikke_lage_foreldrelost_gjoremal(
    client: TestClient, liste: dict, db_path: Path
) -> None:
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()
    client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": 999})
    assert _foreldrelose(db_path) == 0


def test_listesletting_kan_ikke_lage_foreldrelost_gjoremal(
    client: TestClient, liste: dict, db_path: Path
) -> None:
    client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"})
    client.delete(f"/lists/{liste['id']}")
    assert _foreldrelose(db_path) == 0


def test_fremmednokkelen_avviser_direkte_innsetting(db_path: Path, client: TestClient) -> None:
    """Databasen håndhever relasjonen, ikke bare API-laget."""
    conn = connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO todos(title, done, list_id) VALUES(?, ?, ?)",
                ("Kjøpe melk", 0, 999),
            )
    finally:
        conn.close()


# --- FR-019: ingen delvis lagrede endringer -----------------------------------


def test_feilet_flytting_etterlater_ingen_endring(client: TestClient, liste: dict) -> None:
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    client.post(f"/todos/{gjoremal['id']}/move", json={"list_id": 999})

    assert client.get(f"/todos/{gjoremal['id']}").json() == gjoremal


def test_feilet_oppretting_etterlater_ingen_rad(
    client: TestClient, liste: dict, db_path: Path
) -> None:
    client.post("/lists/999/todos", json={"title": "Kjøpe melk"})

    conn = connect(db_path)
    try:
        assert conn.execute("SELECT count(*) FROM todos").fetchone()[0] == 0
    finally:
        conn.close()


def test_avvist_endring_etterlater_ingen_endring(client: TestClient, liste: dict) -> None:
    gjoremal = client.post(f"/lists/{liste['id']}/todos", json={"title": "Kjøpe melk"}).json()

    client.patch(f"/todos/{gjoremal['id']}", json={"title": "  ", "done": True})

    assert client.get(f"/todos/{gjoremal['id']}").json() == gjoremal
