---

description: "Task list for Todo Lists API implementation"
---

# Tasks: Todo Lists API

**Input**: Design documents from `specs/001-todo-lists-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: INCLUDED. Not optional here — the constitution's Development Workflow
requires "the happy path and the not-found path for every endpoint, plus one
test proving data survives a reopened database connection".

**Organization**: Grouped by user story so each is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: US1–US4, mapping to the user stories in spec.md
- Paths are relative to the track root `spor/spec-kit/`, where `make run`,
  `make test` and `make lint` are invoked

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package skeleton and the import path the tests depend on

- [X] T001 Create the package skeleton: empty `todo/__init__.py` and `todo/routers/__init__.py`, plus the `tests/` directory
- [X] T002 Create `conftest.py` at the track root containing only a `sys.path` insert of its own directory, so pytest's prepend import mode can resolve `import todo` from `tests/` (per plan.md Structure Decision)
- [X] T003 [P] Create `.gitignore` at the track root ignoring `data/`, `__pycache__/` and `*.db`, so the runtime SQLite file is never committed
- [X] T004 Confirm the toolchain baseline: run `make install`, then `make lint` and `make test` on the empty tree and confirm both succeed (pytest exit code 5 "no tests" is accepted by the Makefile)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Storage, error handling, schemas and app wiring that every user story needs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `todo/db.py`: resolve the database path from `TODO_DB_PATH` else `data/todo.db` relative to the package directory via `Path(__file__)` (never the cwd), create the parent directory on demand, expose a `connect()` factory that sets `row_factory = sqlite3.Row` and executes `PRAGMA foreign_keys = ON` on every connection (SQLite defaults it OFF and the cascade depends on it — research.md D2, D7, D8)
- [X] T006 Add the schema DDL and `init_db()` to `todo/db.py` exactly as in data-model.md: `lists(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)`; `todos(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0,1)), list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE)`; `CREATE INDEX IF NOT EXISTS idx_todos_list_id ON todos(list_id)`. Every statement uses `IF NOT EXISTS` so a fresh and an existing file behave identically
- [X] T007 Add the request-scoped connection dependency `get_db()` to `todo/db.py`: open per request, `yield`, close in a `finally`. Do not create a module-level shared connection — FastAPI runs sync handlers in a thread pool (research.md D7)
- [X] T008 [P] Implement `todo/errors.py`: a `NotFoundError(Exception)` carrying `resource` and a human-readable `message`, plus an exception handler returning `JSONResponse(status_code=404, content={"detail": message})`. Message forms per contracts: `"List {id} not found"`, `"Todo {id} not found"`, `"Todo {tid} not found in list {lid}"`
- [X] T009 [P] Implement `todo/schemas.py` with Pydantic v2 models — `ListCreate`/`ListUpdate` (field `name`), `ListOut` (`id`, `name`), `TodoCreate` (`title`, optional `done` defaulting to `False`), `TodoUpdate` (`title` and `done` both optional), `TodoMove` (`list_id`), `TodoOut` (`id`, `title`, `done`, `list_id`). Every `name`/`title` is `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]` so whitespace is trimmed before the non-empty check (FR-014, research.md D9)
- [X] T010 Add a validator to `TodoUpdate` in `todo/schemas.py` rejecting a body where no field was set, so an empty PATCH body is a 422 rather than a silent no-op (data-model.md validation rules). `ListUpdate` needs no validator: `name` is its only mutable field, so declaring it required already produces the same 422 — noted during implementation
- [X] T011 Implement `todo/main.py`: create the FastAPI app, call `init_db()` on startup via a lifespan handler, register the `NotFoundError` handler from `todo/errors.py`, and expose the app as the module-level name `app` so `make run APP=todo.main:app` works (plan.md Technical Context)
- [X] T012 Implement `tests/conftest.py`: a fixture that points `TODO_DB_PATH` at a fresh file under pytest's `tmp_path` for each test, runs `init_db()`, and yields a `TestClient`. Each test MUST get its own file so no test sees another's rows

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 - Capture todos in a named list (Priority: P1) 🎯 MVP

**Goal**: Create a list, add todos to it, read them back, and find them still there after a restart

**Independent Test**: Create a list, add two todos, `GET /lists/{id}/todos` and see exactly those two with the titles given and `done: false`; reopen the database and read them again

### Tests for User Story 1

- [X] T013 [P] [US1] Write `tests/test_lists.py` covering R1/R2/R3: creating a list returns 201 with a system-assigned `id` and the given `name`; `GET /lists` returns all lists in creation order; `GET /lists/{id}` returns one
- [X] T014 [P] [US1] Write `tests/test_list_todos.py` covering R6/R7: a todo created in a list returns 201 with `done: false` and the correct `list_id`; the list's todos contain exactly its own todos and none from another list; an existing list with no todos returns `200 []`, never 404 (contract invariant 4)
- [X] T015 [P] [US1] Write `tests/test_persistence.py`: create a list and a todo, dispose of the app and open a second `TestClient` against the same `TODO_DB_PATH` file, and assert the same ids, titles, `done` values and `list_id` come back (FR-015, SC-004, Constitution Principle II)

### Implementation for User Story 1

- [X] T016 [US1] Implement list reads and creation in `todo/repository.py`: `create_list(conn, name)` returning the new row, `get_list(conn, list_id)` raising `NotFoundError` when absent, `list_lists(conn)` ordered by `id`. Commit inside the writing function
- [X] T017 [US1] Implement todo creation and per-list reads in `todo/repository.py`: `create_todo(conn, list_id, title, done)` which first resolves the list so a missing one is a 404 and no row is written (FR-012), and `list_todos(conn, list_id)` ordered by `id` which also resolves the list first so a missing list is 404 rather than an empty array
- [X] T018 [US1] Implement `todo/routers/lists.py` with R1 `POST /lists` (201), R2 `GET /lists`, R3 `GET /lists/{list_id}`, using `get_db` and the `ListOut` schema
- [X] T019 [US1] Add R6 `GET /lists/{list_id}/todos` and R7 `POST /lists/{list_id}/todos` (201) to `todo/routers/lists.py`, returning `TodoOut` with `list_id` populated so a client never needs a second request to learn membership (FR-018)
- [X] T020 [US1] Include the lists router in `todo/main.py` and confirm `tests/test_lists.py`, `tests/test_list_todos.py` and `tests/test_persistence.py` pass

**Checkpoint**: The MVP works — lists and todos can be created, read back, and survive a restart

---

## Phase 4: User Story 2 - Predictable answers for things that do not exist (Priority: P1)

**Goal**: Every operation aimed at a missing resource returns a 404 naming what was missing, never a 500, and the service keeps serving

**Independent Test**: Aim each route at an identifier known not to exist, assert 404 and a `detail` naming the resource, then issue a valid request and assert it still succeeds

**Note**: Shares the P1 priority with US1 because it applies to US1's routes from the moment they exist; it is listed second only because it needs routes to aim at.

### Tests for User Story 2

- [X] T021 [P] [US2] Write `tests/test_not_found.py` covering the not-found column of the contract route table: R3/R4/R5/R6/R7 with a missing list, R9/R10/R11 with a missing todo, R8 with a todo that exists but in another list, and R12 with a missing destination list. Assert status 404, a `detail` string naming the resource, and — critically — assert the response is not 500 and that a following valid request returns 200
- [X] T022 [P] [US2] Add to `tests/test_not_found.py` the no-side-effect assertions: creating a todo under a missing list leaves the todo count unchanged (US2 scenario 2), and a failed move leaves the todo in its original list (US4 scenario 3)

### Implementation for User Story 2

- [X] T023 [US2] Ensure every lookup in `todo/repository.py` raises `NotFoundError` rather than returning `None`, so no router branches on absence and no path can return `None` into a response model (research.md D3)
- [X] T024 [US2] Implement R8 `GET /lists/{list_id}/todos/{todo_id}` in `todo/routers/lists.py` backed by a repository function using a single `WHERE id = ? AND list_id = ?` query, raising `NotFoundError` with the `"Todo {tid} not found in list {lid}"` message. The membership check is the query, not a second round trip (FR-017, research.md D6)
- [X] T025 [US2] Verify the handler registered in T008 is the only place a 404 is produced: grep `todo/routers/` for `HTTPException` and `status_code=404` and confirm there are no per-route 404s

**Checkpoint**: Missing resources are handled identically across all routes, from one place

---

## Phase 5: User Story 3 - Track and revise work (Priority: P2)

**Goal**: Mark todos done and undone, correct titles, rename lists, delete todos and lists

**Independent Test**: Create a todo, mark it done and read the status back, rename it and confirm the status survived, delete it and confirm it is gone from its list

### Tests for User Story 3

- [X] T026 [P] [US3] Write `tests/test_todos.py` covering R9/R10/R11: setting `done: true` then back to `false`; a title-only PATCH leaving `done` and `list_id` untouched and a `done`-only PATCH leaving the title untouched (FR-008); delete returning 204 and the todo then absent from its list
- [X] T027 [P] [US3] Add list update and delete coverage to `tests/test_lists.py` for R4/R5: renaming keeps the same `id` and the same todos; deleting a list holding todos returns 204 and every one of those todos is then 404 on `GET /todos/{id}` (FR-016, cascade — the assertion that proves `PRAGMA foreign_keys = ON` actually took effect)
- [X] T028 [P] [US3] Write `tests/test_validation.py`: empty and whitespace-only `name` and `title` on create and update return 422, not 404 and not 500 (FR-014); a PATCH with an empty body returns 422; a non-integer id in the path returns 422; a title with `æ ø å` round-trips unchanged while surrounding spaces are trimmed (spec edge cases)

### Implementation for User Story 3

- [X] T029 [US3] Implement `update_list(conn, list_id, name)` and `delete_list(conn, list_id)` in `todo/repository.py`, both resolving the list first so a missing one is 404. Deletion relies on `ON DELETE CASCADE` — do not delete the todos in Python (research.md D2)
- [X] T030 [US3] Implement `update_todo(conn, todo_id, fields)` and `delete_todo(conn, todo_id)` in `todo/repository.py`, building the `SET` clause from the `exclude_unset` payload with parameterised placeholders so an omitted field is never written (FR-008, research.md D4)
- [X] T031 [US3] Add R4 `PATCH /lists/{list_id}` and R5 `DELETE /lists/{list_id}` (204, empty body) to `todo/routers/lists.py`
- [X] T032 [US3] Implement `todo/routers/todos.py` with R9 `GET /todos/{todo_id}`, R10 `PATCH /todos/{todo_id}` and R11 `DELETE /todos/{todo_id}` (204), and include the router in `todo/main.py`

**Checkpoint**: Full CRUD on both entities; US1 and US2 still pass

---

## Phase 6: User Story 4 - Move a todo to another list (Priority: P3)

**Goal**: Move a todo between existing lists without losing its identifier, title or status

**Independent Test**: Move a todo from list A to list B; confirm it appears in B's todos, is gone from A's, and kept its `id`, `title` and `done`

### Tests for User Story 4

- [X] T033 [P] [US4] Write `tests/test_move.py` covering R12: a successful move preserves `id`, `title` and `done` and reports the new `list_id`; the source list no longer lists it and the destination does; moving to a non-existent list returns 404 naming the **destination list** (not the todo) and leaves membership unchanged; moving a todo to the list it is already in returns 200 with the todo unchanged (US4 scenario 4)

### Implementation for User Story 4

- [X] T034 [US4] Implement `move_todo(conn, todo_id, list_id)` in `todo/repository.py`: resolve the todo first, then the destination list, then a single `UPDATE todos SET list_id = ? WHERE id = ?`. Resolving in that order is what makes a missing destination report the list rather than the todo (contracts/http-api.md, research.md D5)
- [X] T035 [US4] Add R12 `POST /todos/{todo_id}/move` taking `TodoMove` to `todo/routers/todos.py`, returning 200 with the updated `TodoOut`

**Checkpoint**: All twelve routes in the contract are implemented

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T036 Run `make test` from `spor/spec-kit/` and confirm every test passes
- [X] T037 Run `make lint` from `spor/spec-kit/` and fix every finding (ruff, line-length 100, rules E/F/I/UP/B)
- [X] T038 Walk `specs/001-todo-lists-api/quickstart.md` against a running `make run APP=todo.main:app`, confirming all six scenarios behave as documented, including the manual restart in Scenario 5
- [X] T039 Verify the route table in `specs/001-todo-lists-api/contracts/http-api.md` against the implemented routes — all twelve present, no extras beyond the brief (Constitution Principles IV and V)
- [X] T040 Verify Principle I by confirming no runtime import outside FastAPI, Pydantic and stdlib `sqlite3`, and that the repo-root `pyproject.toml` is unmodified
- [X] T041 [P] Add a short `README` section or module docstrings stating how to run the service, where the database file lives and how `TODO_DB_PATH` overrides it

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: needs Setup — BLOCKS all user stories
- **US1 (Phase 3)**: needs Foundational
- **US2 (Phase 4)**: needs Foundational; T021/T022 need US1's routes to exist to aim at, and T024 extends the lists router from T019
- **US3 (Phase 5)**: needs Foundational; touches the same two router files as US1, so it does not run concurrently with Phase 3
- **US4 (Phase 6)**: needs Foundational and the todos router created in T032
- **Polish (Phase 7)**: needs all of the above

### Within Each User Story

- Tests are written first and must fail before the implementation tasks
- Repository functions before the routers that call them
- Routers before wiring them into `todo/main.py`

### Parallel Opportunities

- T003 runs alongside T001/T002
- T008 and T009 are different files and run in parallel
- All test-writing tasks within a story ([P]) are different files and run in parallel: T013/T014/T015; T021/T022; T026/T027/T028
- Stories cannot be fully parallelised here despite being independently testable: US1, US2 and US3 all write to `todo/routers/lists.py` and `todo/repository.py`. Sequencing by priority is the honest execution order for a single implementer

### Parallel Example: User Story 1

```text
# After Phase 2 completes, write the three test files together:
T013 tests/test_lists.py
T014 tests/test_list_todos.py
T015 tests/test_persistence.py
# then implement T016 → T017 → T018 → T019 → T020 in order
```

---

## Implementation Strategy

**MVP scope**: Phases 1–3 (T001–T020). That delivers lists, todos inside them,
reading a list's todos, and durable storage — a usable API on its own.

**Incremental delivery**:

1. Phases 1–2 — foundation, nothing user-visible
2. Phase 3 — MVP, demonstrable: create a list, add todos, restart, read them back
3. Phase 4 — the API stops being brittle at the edges
4. Phase 5 — todos become maintainable over time
5. Phase 6 — the last explicit requirement from the brief
6. Phase 7 — verification against the constitution and the quickstart

**Total**: 41 tasks — 4 setup, 8 foundational, 8 (US1), 5 (US2), 7 (US3),
3 (US4), 6 polish.
