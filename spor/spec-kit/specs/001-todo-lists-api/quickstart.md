# Quickstart: Todo Lists API

How to run the service and verify it satisfies the spec. Route details are in
[contracts/http-api.md](./contracts/http-api.md); the schema is in
[data-model.md](./data-model.md).

## Prerequisites

Run everything from `spor/spec-kit/`. Dependencies (FastAPI, Pydantic, uvicorn,
pytest, httpx, ruff) are already declared in the repo-root `pyproject.toml`;
this feature adds none.

```bash
make install
```

## Run the service

```bash
make run APP=todo.main:app
```

Serves on `http://127.0.0.1:8000`. Interactive docs at `/docs`. The database
file is created on first start at `todo/../data/todo.db`; set `TODO_DB_PATH` to
point elsewhere.

## Run the checks

```bash
make test   # pytest
make lint   # ruff, line-length 100, rules E/F/I/UP/B
```

Both must pass before the feature is considered done (Constitution, Development
Workflow).

## Scenario 1 — Capture todos in a list (US1)

```bash
curl -sX POST localhost:8000/lists \
  -H 'content-type: application/json' -d '{"name":"Handleliste"}'
# → {"id":1,"name":"Handleliste"}

curl -sX POST localhost:8000/lists/1/todos \
  -H 'content-type: application/json' -d '{"title":"Kjøpe melk"}'
# → {"id":1,"title":"Kjøpe melk","done":false,"list_id":1}

curl -s localhost:8000/lists/1/todos
# → [{"id":1,"title":"Kjøpe melk","done":false,"list_id":1}]
```

**Expected**: the todo comes back with the title given, `done` false, and the
`list_id` of the list it was created in.

## Scenario 2 — Missing things answer cleanly (US2)

```bash
curl -si localhost:8000/lists/99 | head -1        # HTTP/1.1 404 Not Found
curl -s  localhost:8000/lists/99                  # {"detail":"List 99 not found"}

curl -siX POST localhost:8000/lists/99/todos \
  -H 'content-type: application/json' -d '{"title":"x"}' | head -1   # 404

curl -si localhost:8000/lists/2/todos/1 | head -1 # 404 — todo 1 is in list 1

curl -si localhost:8000/lists/1 | head -1         # 200 — still serving
```

**Expected**: every miss is a 404 with a body naming what was missing, no 500,
and the service answers the next valid request normally.

## Scenario 3 — Track and revise (US3)

```bash
curl -sX PATCH localhost:8000/todos/1 \
  -H 'content-type: application/json' -d '{"done":true}'
# → {"id":1,"title":"Kjøpe melk","done":true,"list_id":1}   title unchanged

curl -sX PATCH localhost:8000/todos/1 \
  -H 'content-type: application/json' -d '{"title":"Kjøpe havremelk"}'
# → done stays true

curl -sX PATCH localhost:8000/lists/1 \
  -H 'content-type: application/json' -d '{"name":"Ukens handel"}'
```

**Expected**: a partial update touches only the fields sent.

## Scenario 4 — Move between lists (US4)

```bash
curl -sX POST localhost:8000/lists \
  -H 'content-type: application/json' -d '{"name":"Senere"}'   # → id 2

curl -sX POST localhost:8000/todos/1/move \
  -H 'content-type: application/json' -d '{"list_id":2}'
# → {"id":1,"title":"Kjøpe havremelk","done":true,"list_id":2}

curl -s localhost:8000/lists/1/todos   # → []
curl -s localhost:8000/lists/2/todos   # → the moved todo

curl -s localhost:8000/todos/1/move \
  -X POST -H 'content-type: application/json' -d '{"list_id":99}'
# → 404 {"detail":"List 99 not found"}, todo still in list 2
```

**Expected**: id, title and done survive the move; a bad destination changes
nothing.

## Scenario 5 — Data survives a restart (SC-004, Principle II)

```bash
# with the service running and data created as above:
# stop it with Ctrl-C, then:
make run APP=todo.main:app

curl -s localhost:8000/lists          # the same lists, same ids
curl -s localhost:8000/lists/2/todos  # the same todo, still done, still in list 2
```

**Expected**: identical ids, titles, statuses and list membership. This is also
asserted automatically in `tests/test_persistence.py`, which reopens the
database file in a second application instance rather than relying on a manual
restart.

## Scenario 6 — Cascade delete

```bash
curl -siX DELETE localhost:8000/lists/2 | head -1   # 204
curl -si  localhost:8000/todos/1 | head -1          # 404 — went with its list
```

**Expected**: no todo outlives its list.

## Validation checklist

| Check | Scenario | Requirement |
| --- | --- | --- |
| Full CRUD on both entities reachable | 1, 3, 6 | FR-001..FR-009 |
| A list's todos retrievable | 1 | FR-007 |
| Move between lists | 4 | FR-010 |
| Every miss is a clean 404 | 2, 4 | FR-012, FR-013 |
| Empty/whitespace names rejected as 422 | `make test` | FR-014 |
| Data survives restart | 5 | FR-015 |
| No todo without a list | 6 | FR-011, FR-016 |
| Todo under the wrong list is 404 | 2 | FR-017 |
| `list_id` on every todo | 1 | FR-018 |
