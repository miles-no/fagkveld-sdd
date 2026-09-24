---
title: 'Story 1.1: Create and fetch Lists'
type: 'feature'
created: '2026-09-24'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No API exists yet. Clients need to create Lists and read them back, including after a restart, before Todos can be added.

**Approach:** Create the `todo_api/` package skeleton per the architecture spine (app factory, per-request connection dependency, `NotFoundError` handler, `lists` table) and expose `POST /lists`, `GET /lists`, `GET /lists/{list_id}`, all covered by pytest tests that exercise Story 1.1's acceptance criteria.

</frozen-after-approval>

## Implementation Notes

- Files: `todo_api/{__init__,main,api,service,repository,db,schemas,errors}.py`, `conftest.py` (at `spor/bmad/` root so `todo_api` is importable and fixtures are shared), `tests/test_lists.py`.
- Only the `lists` table is created in this story; `todos` arrives in Story 1.2.
- Run tests with `make test` from `spor/bmad/`.
- `get_connection` uses `Depends(..., scope="function")` so the commit happens before the response is sent; `check_same_thread=False` because FastAPI may run the dependency and route on different pool threads.
- `init_db` runs in the app lifespan, not at import, so importing `todo_api.main` creates no database file. Tests use `with TestClient(...)` to trigger lifespan.
- Track `.gitignore` left as committed; the repo root already ignores `*.db`.

## Review Triage Log

- Todos missing: false. Out of scope for Story 1.1; covered by Stories 1.2 and 1.3.
- List update/delete missing: false. Story 1.4; cascade rule is recorded in AD-4.
- FastAPI floor below `scope` support: medium, deferred. Root `pyproject.toml` is shared and outside the track; `uv.lock` pins 0.141.1.
- DB path relative to CWD: low, deferred. Conforms to AD-7; changing it is an architecture amendment.
- App created at import time: false. `create_app` only resolves a path; the DB is created in lifespan, verified no `todo.db` appears on import.
- No max length on names: low, rejected. No requirement for it; adds a new rule users would notice.
- 404 body has only prose: false. Body shape is fixed by AD-3.
- Whitespace test lacks status assertion: low, patched.
- No test for non-integer id: low, patched.
- No rollback test: low, rejected. No multi-statement write exists yet that could partially fail.
- Schema can't evolve: false for this plan. Story 1.2 adds a new table, which `CREATE TABLE IF NOT EXISTS` handles; migrations are deferred in the spine.
- Redundant `.gitignore`: false. The track `.gitignore` predates this story and does not list `todo.db`; my overwrite was reverted.
