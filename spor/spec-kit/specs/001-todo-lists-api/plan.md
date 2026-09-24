# Implementation Plan: Todo Lists API

**Branch**: `spor/agent-os` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-todo-lists-api/spec.md`

## Summary

An HTTP API over two resources — lists and the todos they hold — backed by a
SQLite file so data survives restarts. Lists and todos each get full create,
read, update and delete; a list exposes its todos; a todo can be moved to
another list. Missing resources are handled in one place: the storage layer
raises a typed not-found error, a single exception handler turns it into a 404
with a JSON body naming what was missing, so no route re-implements the rule.

Three layers, each earning its place under Constitution Principle V: Pydantic
schemas own input validation, a repository owns all SQL and the not-found
signal, and thin routers own only HTTP shape. Referential integrity (a todo
always has a list, and a deleted list takes its todos with it) is pushed into
the database as a foreign key with `ON DELETE CASCADE` rather than being
re-implemented in Python.

## Technical Context

**Language/Version**: Python 3.12+ (repo requires `>=3.12`; local interpreter 3.13.7)

**Primary Dependencies**: FastAPI, Pydantic v2, `sqlite3` from the standard
library. All are already declared in the repo-root `pyproject.toml`; this
feature adds none.

**Storage**: A single SQLite file. Path from the `TODO_DB_PATH` environment
variable, defaulting to `data/todo.db` resolved relative to the package, so the
location does not depend on the working directory.

**Testing**: pytest with FastAPI's `TestClient` (httpx), both already in the
repo's dev dependency group. Each test gets a fresh database file in a tmp dir.

**Target Platform**: Local Linux/macOS process served by uvicorn via
`make run APP=todo.main:app`

**Project Type**: Single web service, no frontend

**Performance Goals**: None set. Per the spec's Assumptions the workload is a
single developer's lists; the requirement is to stay responsive, not to hit a
throughput number.

**Constraints**: No dependency outside the locked stack. Data MUST survive a
process restart. No request may produce an unhandled exception for a missing
resource. `make test` and `make lint` (ruff, line-length 100, rules E/F/I/UP/B)
must pass.

**Scale/Scope**: Two entities, eleven routes, one SQLite file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Pre-Phase 0 | Post-Phase 1 |
| --- | --- | --- | --- |
| I. Locked Stack, Zero New Dependencies | Runtime imports limited to FastAPI, Pydantic, stdlib `sqlite3`; no manifest change | PASS — all three already declared at repo root | PASS — design adds no import outside the set; no ORM or migration tool |
| II. Durable Persistence | Data in a SQLite file; idempotent schema creation; no in-memory system of record | PASS | PASS — `CREATE TABLE IF NOT EXISTS` at startup; file path independent of cwd; a test reopens the file to prove it |
| III. Absence Is A Normal Answer | Every identifier-resolving path returns a deliberate 404 with a JSON body, never a 500 | PASS | PASS — one `NotFoundError` raised by the repository, one handler; nested todo reads verify list membership |
| IV. Complete Resource Coverage | CRUD for both entities, todos-of-a-list, move between lists, every todo always in exactly one list | PASS | PASS — see the route table in [contracts/](./contracts/); the always-in-a-list rule is a `NOT NULL` foreign key, deletion an `ON DELETE CASCADE` |
| V. Build The Brief, Nothing More | No auth, users, tags, due dates, priorities, pagination, soft deletes; every layer justified | PASS | PASS — three layers, each justified in [research.md](./research.md); no field beyond id/name and id/title/done/list_id |

**Result**: All gates pass at both checkpoints. Complexity Tracking is therefore
empty — no violation needs justification.

Technology-constraint checks from the constitution's Technology Constraints
section: `PRAGMA foreign_keys = ON` is set per connection (SQLite defaults it
off, and Principle IV's guarantees depend on it); each request takes and closes
its own connection via a FastAPI dependency, so no connection is shared across
threads; the ASGI app is exposed as the module-level `todo.main:app` so
`make run APP=todo.main:app` works.

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-lists-api/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── http-api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (track root: `spor/spec-kit/`)

```text
spor/spec-kit/
├── conftest.py              # puts the track root on sys.path for pytest
├── todo/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, router wiring, error handler, startup schema init
│   ├── db.py                # db path, connection factory, schema DDL, request dependency
│   ├── errors.py            # NotFoundError + the handler that renders it as 404
│   ├── schemas.py           # Pydantic request/response models and field validation
│   ├── repository.py        # every SQL statement; raises NotFoundError
│   └── routers/
│       ├── __init__.py
│       ├── lists.py         # /lists routes, including a list's todos
│       └── todos.py         # /todos routes, including move
├── data/                    # created at runtime; holds todo.db (git-ignored)
└── tests/
    ├── conftest.py          # fresh temp database + TestClient per test
    ├── test_lists.py
    ├── test_todos.py
    ├── test_list_todos.py
    ├── test_move.py
    ├── test_not_found.py
    ├── test_validation.py
    └── test_persistence.py
```

**Structure Decision**: A single flat package `todo/` at the track root, split
by responsibility rather than by entity, with the two routers being the only
per-entity split. The track root is the import root because `make run`,
`make test` and `make lint` are all invoked from `spor/spec-kit/` per the
track README. `conftest.py` at that root is what makes `import todo` work under
pytest's default prepend import mode; without it, tests collected from `tests/`
would not see the package. No `src/` layer is introduced — there is one
deliverable package and nothing to disambiguate it from.

## Complexity Tracking

No Constitution Check violations. This section is intentionally empty.
