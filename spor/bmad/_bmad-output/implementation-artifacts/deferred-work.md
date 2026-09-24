- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-create-and-fetch-lists.md`
  summary: Raise the `fastapi` floor in the repo-root `pyproject.toml` to a version that supports `Depends(..., scope=...)`.
  evidence: `todo_api/api.py` uses `scope="function"`; `pyproject.toml` allows `fastapi>=0.115`, which predates it. `uv.lock` pins 0.141.1, so locked installs work. The root pyproject is shared by all tracks and is outside this track's folder.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-1-create-and-fetch-lists.md`
  summary: Default database path `todo.db` is relative to the working directory, so starting uvicorn elsewhere opens an empty database.
  evidence: `todo_api/db.py` `DEFAULT_DB_PATH`; matches architecture AD-7 as written. Fixing it means amending AD-7 (anchor to package dir or require `TODO_DB_PATH`).
