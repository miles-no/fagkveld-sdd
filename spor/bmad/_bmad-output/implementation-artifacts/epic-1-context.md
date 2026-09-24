# Epic 1 Context: Manage Todos in persistent Lists

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver an HTTP API where a client can organise Todos in named Lists, mark them done, move them between Lists, and delete what it no longer needs. Data survives an application restart, and requests for anything that does not exist get a predictable not-found answer instead of an error.

## Stories

- Story 1.1: Create and fetch Lists
- Story 1.2: Create Todos and read them per List
- Story 1.3: Update, move and delete Todos
- Story 1.4: Rename and delete Lists

## Requirements & Constraints

- Domain: a List has an id and a non-empty name (duplicates allowed). A Todo has an id, a non-empty title, a done flag (default false), and belongs to exactly one List.
- Full CRUD for Lists and Todos, fetch Todos per List, move a Todo between Lists.
- Deleting a List deletes its Todos (assumption, not yet confirmed by the product owner).
- All data persists across restarts.
- Not-found and validation failures use one consistent status code and body shape; no client-caused condition may return 5xx.
- Stack locked: FastAPI, Pydantic, stdlib `sqlite3`. No new dependencies. Python 3.12.
- Every acceptance criterion covered by a passing automated test. No endpoints beyond what the requirements need.
- Out of scope: auth, multi-user, pagination, filtering, sorting, due dates, UI.

## Technical Decisions

- **Layers:** `api.py` → `service.py` → `repository.py` → `db.py`. Dependencies point downward only. Shared `schemas.py` (Pydantic) and `errors.py` (`NotFoundError`). Package `todo_api/` in `spor/bmad/`, tests in `spor/bmad/tests/`.
- **SQL isolation:** only `repository.py` and `db.py` import `sqlite3`. Repository functions take a `sqlite3.Connection` first and return data or `None`.
- **Connections:** `db.get_connection` FastAPI dependency: open, `PRAGMA foreign_keys = ON`, `row_factory = sqlite3.Row`, yield, commit on success, rollback on exception, close. Repository and service never commit or roll back.
- **Not-found:** repository returns `None`; service raises `NotFoundError(entity, id)`; one handler in the app factory returns 404 `{"detail": "<Entity> <id> not found"}`. Routes never build 404s. Validation uses FastAPI's default 422.
- **Schema:** `db.init_db(path)` runs `CREATE TABLE IF NOT EXISTS` at startup; no drops, no migration tool. `todos.list_id` is `NOT NULL REFERENCES lists(id) ON DELETE CASCADE`. Tables: `lists(id, name)`, `todos(id, title, done INTEGER 0/1, list_id)`, ids `INTEGER PRIMARY KEY AUTOINCREMENT`.
- **Config:** `main.create_app(db_path=None)`; when `None`, path from env `TODO_DB_PATH`, default `todo.db`. Module-level `app = create_app()`. Tests pass a temp path.
- **Todo mutation:** `PATCH /todos/{todo_id}` accepts any subset of `title`, `done`, `list_id` via `model_dump(exclude_unset=True)`; move is `list_id` on PATCH, target List existence checked first. No separate move endpoint.
- **API conventions:** paths `/lists`, `/lists/{list_id}`, `/lists/{list_id}/todos`, `/todos`, `/todos/{todo_id}`; no trailing slash. Create 201 with body, get/patch 200, delete 204 no body. snake_case JSON: List `{id, name}`, Todo `{id, title, done, list_id}`. Collections are bare arrays ordered by id ascending. Pydantic names `ListCreate`, `ListUpdate`, `ListRead`, `TodoCreate`, `TodoUpdate`, `TodoRead`; `name`/`title` stripped and `min_length=1`.
- **Tests:** pytest + FastAPI `TestClient`, fresh DB file per test.

## Cross-Story Dependencies

- 1.1 creates the package skeleton, connection dependency, error handler and `lists` table; all later stories build on it.
- 1.2 adds the `todos` table with the cascading foreign key that 1.4 relies on.
- 1.3 and 1.4 depend only on 1.1 and 1.2.
