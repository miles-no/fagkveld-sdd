<!--
Sync Impact Report
==================
Version change: (none, unratified template) → 1.0.0
Bump rationale: MAJOR — initial ratification. The file previously held only
unfilled template placeholders, so this is the first governing version.

Modified principles:
  [PRINCIPLE_1_NAME] → I. Locked Stack, Zero New Dependencies
  [PRINCIPLE_2_NAME] → II. Durable Persistence
  [PRINCIPLE_3_NAME] → III. Absence Is A Normal Answer
  [PRINCIPLE_4_NAME] → IV. Complete Resource Coverage
  [PRINCIPLE_5_NAME] → V. Build The Brief, Nothing More

Added sections:
  [SECTION_2_NAME] → Technology Constraints
  [SECTION_3_NAME] → Development Workflow

Removed sections: none

Follow-up TODOs: none. All placeholder tokens resolved.
-->

# TODO API Constitution

## Core Principles

### I. Locked Stack, Zero New Dependencies

The runtime stack is FastAPI, Pydantic and the standard library's `sqlite3`.
No dependency outside that set MUST be added to the runtime application, and
no ORM, migration framework or database driver MAY be introduced. Test and
lint tooling already present in the project (pytest, ruff, uvicorn) is
permitted; adding anything further requires an amendment to this document.

Rationale: The brief locks the stack explicitly. The constraint is the
exercise, not an accident, so it is enforced as a hard gate rather than a
preference.

### II. Durable Persistence

All application data MUST live in a SQLite database file on disk. Restarting
the process MUST NOT lose or alter data. In-memory storage, module-level
dictionaries or per-process caches MUST NOT be the system of record. The
schema MUST be created idempotently at startup so a fresh checkout and an
existing database both work without manual steps.

Rationale: "Data skal overleve en omstart av applikasjonen" is a stated
requirement, and it is the one requirement an in-memory shortcut silently
violates while every test still passes.

### III. Absence Is A Normal Answer

A request for a resource that does not exist is an expected outcome, not a
fault. Such requests MUST produce a deliberate, documented response — an HTTP
404 with a JSON body explaining what was not found — and MUST NOT raise an
unhandled exception, return a 500, or leak a stack trace. Every path that
resolves an identifier, including nested and cross-resource paths such as
moving a todo into a list, MUST validate existence before acting.

Rationale: The brief calls this out by name. It is the single behaviour most
likely to be handled inconsistently across endpoints, so it is stated as a
principle rather than left to each handler.

### IV. Complete Resource Coverage

Both lists and todos MUST support create, read, update and delete through the
API. In addition the API MUST expose retrieval of the todos belonging to a
given list, and moving a todo from one list to another. A todo MUST belong to
exactly one list at all times; no todo may exist without a list, and deleting
a list MUST define and implement an explicit, documented behaviour for the
todos it holds.

Rationale: These are the functional requirements. Listing them as a principle
makes an incomplete surface a governance failure rather than a missing ticket.

### V. Build The Brief, Nothing More

Features not required by the brief — authentication, users, tags, due dates,
priorities, pagination beyond need, soft deletes, background jobs — MUST NOT
be added. Code organisation, naming and API shape are free choices, but each
layer or abstraction MUST earn its place by serving a stated requirement.
When two designs satisfy the brief, the simpler one MUST be chosen.

Rationale: The brief grants wide freedom over structure. That freedom invites
speculative scope; this principle converts the freedom into an explicit budget.

## Technology Constraints

- Runtime: Python with FastAPI and Pydantic for the HTTP surface and
  validation; `sqlite3` from the standard library for storage.
- Persistence: a single SQLite file. Foreign keys MUST be enforced by the
  connection (`PRAGMA foreign_keys = ON`), since SQLite leaves them off by
  default and the todo→list relationship depends on them.
- Concurrency: each request MUST obtain and release its own connection, or
  use a connection explicitly configured for cross-thread use. A connection
  MUST NOT be shared implicitly across threads.
- Execution: the app runs via `make run APP=<module>:<variable>`, so the
  ASGI application MUST be importable as a module-level variable.

## Development Workflow

- Spec Kit order is binding: constitution → specify → plan → tasks →
  implement. A later artifact MUST NOT contradict an earlier one; if it must,
  the earlier artifact is amended first.
- `make test` and `make lint` MUST both pass before work is reported complete.
- Tests MUST cover the happy path and the not-found path for every endpoint,
  plus one test proving data survives a reopened database connection.
- Technical decisions belong in `plan.md`, not in `spec.md`.

## Governance

This constitution supersedes other practices for this track. Every later Spec
Kit artifact — spec, plan, tasks, implementation — MUST be checked against it,
and any deviation MUST be recorded in the plan's Complexity Tracking section
with a justification, or else removed.

Amendments require: a written statement of the change, a version bump per the
policy below, and an update to any artifact the change invalidates.

Versioning policy (semantic):
- MAJOR: a principle is removed or redefined incompatibly.
- MINOR: a principle or section is added, or guidance materially expanded.
- PATCH: clarification or wording with no change in obligation.

Compliance review: the implementation step verifies each principle before
reporting completion. Principle I is verifiable from the dependency manifest,
II and III from tests, IV from the route table, and V by review.

**Version**: 1.0.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
