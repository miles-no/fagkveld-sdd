import pytest
from fastapi.testclient import TestClient
from todo_api.main import create_app


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def client(db_path):
    return TestClient(create_app(db_path))


def make_list(client, name="Handel"):
    r = client.post("/lists", json={"name": name})
    assert r.status_code == 201
    return r.json()


def make_todo(client, list_id, title="Melk"):
    r = client.post("/todos", json={"title": title, "list_id": list_id})
    assert r.status_code == 201
    return r.json()


def test_list_crud(client):
    lst = make_list(client)
    assert lst == {"id": lst["id"], "name": "Handel"}
    assert client.get(f"/lists/{lst['id']}").json() == lst
    assert client.get("/lists").json() == [lst]

    r = client.patch(f"/lists/{lst['id']}", json={"name": "Butikk"})
    assert r.json()["name"] == "Butikk"

    assert client.delete(f"/lists/{lst['id']}").status_code == 204
    assert client.get(f"/lists/{lst['id']}").status_code == 404


def test_todo_crud(client):
    lst = make_list(client)
    todo = make_todo(client, lst["id"])
    assert todo == {"id": todo["id"], "title": "Melk", "done": False, "list_id": lst["id"]}
    assert client.get(f"/todos/{todo['id']}").json() == todo

    r = client.patch(f"/todos/{todo['id']}", json={"done": True})
    assert r.json() == {**todo, "done": True}
    r = client.patch(f"/todos/{todo['id']}", json={"title": "Brød"})
    assert r.json() == {**todo, "done": True, "title": "Brød"}

    assert client.delete(f"/todos/{todo['id']}").status_code == 204
    assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_todos_in_list(client):
    a, b = make_list(client, "A"), make_list(client, "B")
    t1 = make_todo(client, a["id"], "1")
    make_todo(client, b["id"], "2")
    assert client.get(f"/lists/{a['id']}/todos").json() == [t1]


def test_move_todo(client):
    a, b = make_list(client, "A"), make_list(client, "B")
    todo = make_todo(client, a["id"])
    r = client.patch(f"/todos/{todo['id']}", json={"list_id": b["id"]})
    assert r.status_code == 200
    assert client.get(f"/lists/{a['id']}/todos").json() == []
    assert client.get(f"/lists/{b['id']}/todos").json() == [{**todo, "list_id": b["id"]}]


def test_move_to_missing_list_is_404_and_unchanged(client):
    lst = make_list(client)
    todo = make_todo(client, lst["id"])
    assert client.patch(f"/todos/{todo['id']}", json={"list_id": 999}).status_code == 404
    assert client.get(f"/todos/{todo['id']}").json() == todo


def test_deleting_list_deletes_its_todos(client):
    lst = make_list(client)
    todo = make_todo(client, lst["id"])
    client.delete(f"/lists/{lst['id']}")
    assert client.get(f"/todos/{todo['id']}").status_code == 404


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/lists/1", None),
        ("patch", "/lists/1", {"name": "x"}),
        ("delete", "/lists/1", None),
        ("get", "/lists/1/todos", None),
        ("get", "/todos/1", None),
        ("patch", "/todos/1", {"done": True}),
        ("delete", "/todos/1", None),
        ("post", "/todos", {"title": "x", "list_id": 1}),
    ],
)
def test_missing_resources_give_404(client, method, path, body):
    kwargs = {"json": body} if body is not None else {}
    r = client.request(method, path, **kwargs)
    assert r.status_code == 404
    assert "finnes ikke" in r.json()["detail"]


@pytest.mark.parametrize(
    "path,body",
    [
        ("/lists", {"name": ""}),
        ("/lists", {"name": "   "}),
        ("/lists", {}),
        ("/todos", {"title": "", "list_id": 1}),
        ("/todos", {"title": "x"}),
    ],
)
def test_invalid_input_gives_422(client, path, body):
    make_list(client)
    assert client.post(path, json=body).status_code == 422


def test_data_survives_restart(db_path):
    first = TestClient(create_app(db_path))
    lst = make_list(first)
    todo = make_todo(first, lst["id"])

    second = TestClient(create_app(db_path))
    assert second.get(f"/lists/{lst['id']}").json() == lst
    assert second.get(f"/todos/{todo['id']}").json() == todo
