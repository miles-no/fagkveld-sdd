"""Røyktest: appen starter, skjemaet finnes, og fremmednøkler er slått på."""

from pathlib import Path

from fastapi.testclient import TestClient
from todo_api.db import connect


def test_appen_svarer(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200


def test_skjemaet_opprettes_ved_oppstart(db_path: Path, client: TestClient) -> None:
    conn = connect(db_path)
    try:
        navn = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        conn.close()
    assert {"lists", "todos"} <= navn


def test_skjemaet_kan_opprettes_to_ganger(db_path: Path, client: TestClient) -> None:
    """init_schema er idempotent — en eksisterende fil skal ikke feile."""
    from todo_api.main import create_app

    create_app(db_path)


def test_fremmednokler_er_slatt_paa(db_path: Path) -> None:
    """PRAGMA foreign_keys er av som standard og må settes per tilkobling.

    Glemmes den, virker alt bortsett fra cascade-sletting, og det oppdages
    først langt senere.
    """
    conn = connect(db_path)
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conn.close()
