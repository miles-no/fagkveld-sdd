# Addendum: Todo & Lists API

Technical notes for architecture. Not requirements.

- Persistence via stdlib `sqlite3` to a file on disk (path configurable, e.g. env var) satisfies FR-11 without new dependencies.
- Enforce Todo → List relationship with a foreign key; enable `PRAGMA foreign_keys = ON` per connection. `ON DELETE CASCADE` implements the assumed FR-4 behaviour.
- FastAPI's default 404/422 conventions are a natural fit for FR-12; keep one error body shape (FastAPI's `{"detail": ...}`) across all endpoints.
- Move (FR-10) can be a dedicated action or a `list_id` field on Todo update; architect's choice.
