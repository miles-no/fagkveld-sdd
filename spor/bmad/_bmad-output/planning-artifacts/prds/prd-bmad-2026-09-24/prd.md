---
title: Todo & Lists API
status: draft
created: 2026-09-24
updated: 2026-09-24
---

# PRD: Todo & Lists API
*Working title; confirm.*

## 0. Document Purpose
This PRD translates `oppgave/krav.md` into testable requirements for a greenfield HTTP API that manages Todos and Lists. It is written for the developer (human or agent) who will design and build the service, and for downstream architecture and story work. Vocabulary is fixed by the Glossary (§3). Inferred decisions are tagged `[ASSUMPTION]` inline and indexed in §9. Technical notes live in `addendum.md`.

## 1. Vision
A small, dependable backend for keeping track of things to do, grouped into named Lists. A client can create Lists, put Todos in them, mark Todos done, move Todos between Lists, and clean up what it no longer needs.

The API treats "not found" as an ordinary answer, not a failure: every request gets a predictable, well-formed response. Data survives an application restart.

## 2. Target User

### 2.1 Jobs To Be Done
- As a client developer, I want to manage Lists and Todos over HTTP with predictable responses so I can build a UI or script on top without special-casing errors.
- As an operator, I want data to persist across restarts with no external services to run.

### 2.2 Key User Journeys
- **UJ-1. Kari organises her week.** Kari's front-end creates a List "Groceries", adds three Todos, fetches the List's Todos to render them, and marks one done.
- **UJ-2. Kari reorganises.** She moves a Todo from "Groceries" to a new List "Hardware store", then deletes the now-empty-of-interest List "Groceries".
- **UJ-3. Stale client.** Kari's app holds an id for a Todo already deleted on another device. Fetching, updating, or moving it returns a clear not-found response; the app shows "already removed" instead of crashing.

## 3. Glossary
- **List** — A named container of Todos. Has an id and a name. Holds zero or more Todos.
- **Todo** — A unit of work. Has an id, a title, and a done status. Belongs to exactly one List at all times.
- **Done status** — Boolean state of a Todo: done or not done.
- **Move** — Changing which List a Todo belongs to.
- **Not-found response** — The API's defined answer when a referenced List or Todo does not exist.

## 4. Features

### 4.1 List management
**Description:** Clients create, read, rename, and delete Lists. Realizes UJ-1, UJ-2.

#### FR-1: Create List
A client can create a List by providing a name.
- Response includes the new List's id and name.
- An empty or missing name is rejected with a validation error. [ASSUMPTION: name must be non-empty; duplicate names allowed]

#### FR-2: Get Lists
A client can fetch a single List by id, and fetch all Lists.
- Fetching a non-existent id returns a not-found response (FR-12).
- Fetching all Lists when none exist returns an empty collection, not an error.

#### FR-3: Update List
A client can change a List's name.
- Same validation as FR-1. Non-existent id returns not-found.

#### FR-4: Delete List
A client can delete a List.
- The List and all its Todos are removed. [ASSUMPTION: cascade delete; see OQ-1]
- Subsequent fetch of the List or any of its former Todos returns not-found.
- Deleting a non-existent List returns not-found.

### 4.2 Todo management
**Description:** Clients create, read, update, and delete Todos, always within a List. Realizes UJ-1, UJ-3.

#### FR-5: Create Todo
A client can create a Todo with a title in a given List.
- Done status defaults to not done. [ASSUMPTION]
- Empty or missing title is rejected with a validation error.
- Creating a Todo in a non-existent List returns not-found; no Todo is created.

#### FR-6: Get Todo
A client can fetch a single Todo by id.
- Response includes id, title, done status, and the id of its List.
- Non-existent id returns not-found.

#### FR-7: Update Todo
A client can change a Todo's title and/or done status.
- Unchanged fields keep their values. [ASSUMPTION: partial update supported]
- Validation as FR-5. Non-existent id returns not-found.

#### FR-8: Delete Todo
A client can delete a Todo.
- Subsequent fetch returns not-found. Deleting a non-existent Todo returns not-found.

### 4.3 List contents and moving
**Description:** Clients read what is in a List and move Todos between Lists. Realizes UJ-1, UJ-2.

#### FR-9: Get Todos in a List
A client can fetch all Todos belonging to a given List.
- Returns only that List's Todos. An existing List with no Todos returns an empty collection.
- Non-existent List returns not-found (distinct from an empty List).

#### FR-10: Move Todo
A client can move a Todo to another List.
- After the move, the Todo appears in the target List's Todos and not in the source List's.
- Title and done status are unchanged.
- Non-existent Todo or non-existent target List returns not-found; nothing changes.
- Moving to the List it is already in succeeds with no change. [ASSUMPTION]

### 4.4 Cross-cutting behaviour

#### FR-11: Persistence
All Lists and Todos survive an application restart.
- Data created before a restart is retrievable, unchanged, after it.

#### FR-12: Predictable error responses
Every request yields a well-formed response; the service never returns an unhandled server error for a client-caused condition.
- Not-found and validation failures each use a consistent status code and a consistent, machine-readable body shape across all endpoints.
- A reference to a non-existent List or Todo never produces a 5xx.

## 5. Constraints
- **Stack locked:** FastAPI, Pydantic, and `sqlite3` from the Python standard library. No new dependencies.
- API shape, code organisation, and naming are the builder's choice.

## 6. Non-Goals / Out of Scope for v1
- Authentication, authorization, multiple users or tenants.
- Pagination, filtering, sorting, search.
- Due dates, priorities, tags, ordering of Todos within a List.
- Todos without a List, or Todos in multiple Lists.
- Front-end or UI.

## 7. Success Metrics
- **SM-1:** Every FR's consequences are covered by an automated test that passes. Validates FR-1 to FR-12.
- **SM-2:** Zero 5xx responses across a test run that exercises every endpoint with non-existent ids. Validates FR-12.
- **SM-C1 (counter-metric):** Endpoint count. Do not add endpoints beyond what the FRs need; breadth is not success.

## 8. Open Questions
1. **OQ-1:** Delete a List that still has Todos: cascade (assumed) or reject? Owner: PM. Blocks FR-4 tests.
2. **OQ-2:** Should List responses embed their Todos, or only via FR-9? Non-blocking; architect's choice.

## 9. Assumptions Index
- §4.1 FR-1: List name non-empty; duplicate names allowed.
- §4.1 FR-4: Deleting a List cascades to its Todos.
- §4.2 FR-5: New Todo defaults to not done.
- §4.2 FR-7: Partial update of Todos.
- §4.3 FR-10: Move to the same List is a no-op success.
- §6: Single-tenant, no auth, no pagination.
