# Phase 0 Research: Todo Lists API

No `NEEDS CLARIFICATION` markers were carried into the Technical Context — the
brief locks the stack and the spec resolved its own open questions. What follows
is therefore the decision record for the choices the brief left open, each with
the alternatives that were weighed and rejected.

## D1 — Identifier type: SQLite `INTEGER PRIMARY KEY AUTOINCREMENT`

**Decision**: Integer ids assigned by the database, declared `AUTOINCREMENT`.

**Rationale**: The spec assumes identifiers are system-assigned and stable for
the lifetime of a resource. Plain `INTEGER PRIMARY KEY` is a rowid alias, and
SQLite may reuse the rowid of a deleted row; a client holding id 3 for a deleted
todo could then silently address a different todo created later. `AUTOINCREMENT`
adds a monotonic guarantee that rules this out. It also makes `ORDER BY id` a
faithful creation order, which is how the spec's stable-ordering assumption is
satisfied without storing a timestamp.

**Alternatives considered**: UUIDs — no collision or reuse concern, but they
cost a text column, lose free creation ordering, and nothing in the brief needs
client-side id generation or cross-system uniqueness. Composite natural keys
(name, title) — rejected outright: the spec explicitly allows duplicate names
and titles.

## D2 — Cascade delete enforced by the database, not by Python

**Decision**: `list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE`,
with `PRAGMA foreign_keys = ON` set on every connection.

**Rationale**: Constitution Principle IV requires that a todo always belongs to
exactly one list. `NOT NULL` plus the foreign key makes an orphan todo
unrepresentable rather than merely unlikely, and `ON DELETE CASCADE` implements
the spec's cascade-on-list-delete assumption in one line instead of a
delete-children-then-parent sequence that could half-fail. The `PRAGMA` is
essential and easy to forget: SQLite ships with foreign key enforcement **off**
by default and silently ignores the constraint without it, so it is set in the
connection factory where no code path can bypass it.

**Alternatives considered**: deleting todos explicitly in the repository before
deleting the list — more code, and it leaves the invariant enforceable only by
the code that remembers to call it. Refusing to delete a non-empty list — a
defensible product choice, but the spec already rejected it as more surprising.

## D3 — One `NotFoundError`, one exception handler

**Decision**: The repository raises `NotFoundError(resource, identifier)`
whenever a lookup resolves nothing. `todo/main.py` registers a single handler
that renders it as HTTP 404 with body `{"detail": "..."}`. Routers contain no
404 logic.

**Rationale**: Principle III is the requirement most likely to be applied
unevenly, because it touches eleven routes. Centralising it means a new route
inherits the behaviour by construction rather than by the author remembering.
`{"detail": ...}` matches FastAPI's own error shape, so not-found and validation
errors read the same way to a client, at no implementation cost.

**Alternatives considered**: each router checking existence and raising
`HTTPException(404)` — the same behaviour spread across eleven sites, each able
to drift. Returning `None` up through the layers and letting routers branch —
the same drift, plus an `Optional` return type on every repository function.
Letting FastAPI's default 500 handler catch it — a direct violation of
Principle III, which forbids the missing-resource case surfacing as an error.

## D4 — PATCH with `exclude_unset` for partial updates

**Decision**: Updates are `PATCH` with every field optional; the router builds
the payload with `model_dump(exclude_unset=True, exclude_none=True)` and a
validator rejects a body that would change nothing.

**Rationale**: FR-008 requires that changing only a todo's title leave its
status and list membership untouched. `PUT` with a full replacement body cannot
express that without the client round-tripping the current state first and
risking a lost update. Pydantic's `exclude_unset` is what distinguishes "field
omitted" from "field explicitly set", which is precisely the distinction the
requirement rests on. `exclude_none` is paired with it so an explicit
`{"title": null}` cannot blank a `NOT NULL` column: for these fields null and
omitted both mean "leave it alone", and a body that means nothing else is a 422.

**Alternatives considered**: `PUT` with a complete body — simpler to implement,
but it fails FR-008 as written. A separate `POST /todos/{id}/complete` toggle —
an extra route for something a general update already covers, and Principle V
rules out the surplus.

## D5 — Move as its own route, `POST /todos/{id}/move`

**Decision**: Moving is a dedicated route taking `{"list_id": <id>}`, not a
`list_id` field on the general `PATCH`.

**Rationale**: FR-010 treats moving as its own capability, and it has a failure
mode the other fields do not: the destination list may not exist, which must
produce a not-found answer that names the *destination*. Folding it into `PATCH`
would mean one route with two distinct not-found meanings (the todo, or the
target list), which is harder to document and to test. A named route also makes
the operation legible in the route table that Principle IV is checked against.

**Alternatives considered**: `PATCH /todos/{id}` accepting `list_id` — fewer
routes, but a muddier contract. `PUT /lists/{id}/todos/{todo_id}` as a
re-parenting operation — RESTfully defensible but obscure to read, and it
duplicates the nested-read path for a write purpose.

## D6 — Nested read verifies membership: `GET /lists/{lid}/todos/{tid}`

**Decision**: Reading a todo through a list checks that the todo actually
belongs to that list, and returns not-found when it does not.

**Rationale**: FR-017 and the spec's US2 scenario 3 require it. Implemented as a
`WHERE id = ? AND list_id = ?` in a single statement, so the check is the query
rather than a second round trip that could race. Without it the nested path
would be decorative — `/lists/99/todos/1` would happily return a todo from list
1 and quietly contradict the contract.

**Alternatives considered**: omitting the nested read and offering only
`GET /todos/{id}` — fewer routes, but FR-017 would have nothing to test against.
Fetching the todo and comparing `list_id` in the router — pushes a storage
concern into the HTTP layer for no gain.

## D7 — One connection per request, via a FastAPI dependency

**Decision**: A dependency opens a `sqlite3` connection per request, sets
`row_factory = sqlite3.Row` and the foreign-key pragma, yields it, and closes it
in a `finally`. Writes commit inside the repository function that performs them.

**Rationale**: The constitution's Technology Constraints forbid implicitly
sharing a connection across threads, and FastAPI runs synchronous route handlers
in a thread pool, so a single module-level connection would be exactly that.
Per-request connections keep `check_same_thread` at its safe default. SQLite
connection setup is cheap — it is a file handle, not a network handshake — so at
this scale there is nothing to pool.

**Alternatives considered**: one global connection with
`check_same_thread=False` — fewer objects, but it disables the protection that
would otherwise catch a real threading bug, and serialises writes on a lock the
code does not control. A connection pool — machinery with no load to justify it,
which Principle V rules out.

## D8 — Database file location from `TODO_DB_PATH`, defaulting relative to the package

**Decision**: `TODO_DB_PATH` if set, otherwise `data/todo.db` resolved from the
package directory, with the parent directory created on demand. Schema DDL runs
at application startup and is idempotent.

**Rationale**: Principle II requires that a fresh checkout and an existing
database both work with no manual step. Resolving from `Path(__file__)` rather
than the working directory means `make run` from the track root and a test
harness invoked from elsewhere address the same file deliberately, instead of
silently creating a second database. The environment variable is what lets each
test get an isolated file without touching the real one.

**Alternatives considered**: a path relative to the working directory — the
classic source of "my data disappeared" when the process is started from another
directory. A hardcoded absolute path — unusable for tests. An in-memory database
in tests only — it would leave the persistence requirement untested, and the
spec makes surviving a restart an explicit success criterion.

## D9 — Validation in Pydantic, with whitespace stripped

**Decision**: Names and titles are `Annotated[str, StringConstraints(
strip_whitespace=True, min_length=1)]`, so surrounding whitespace is trimmed
before the length check and an empty or whitespace-only value is rejected with
FastAPI's standard 422.

**Rationale**: FR-014 requires invalid input to be distinguishable from
not-found; 422 against 404 makes that distinction without inventing an error
format. Stripping before validating is what makes `"   "` fail rather than pass
as a three-character title, and it satisfies the spec's edge case about trimming
surrounding whitespace while preserving `æ ø å` inside the value.

**Alternatives considered**: validating in the repository — it would reject the
same values but only after the request reached storage, and would not produce a
field-level error message. Accepting empty titles — contradicts FR-014.
