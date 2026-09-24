---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-bmad-2026-09-24/prd.md
  - _bmad-output/planning-artifacts/prds/prd-bmad-2026-09-24/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-bmad-2026-09-24/ARCHITECTURE-SPINE.md
---

# Todo & Lists API - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Todo & Lists API, decomposing the requirements from the PRD and the Architecture spine into implementable stories. There is no UX design; the product is an API only.

## Requirements Inventory

### Functional Requirements

- FR1: A client can create a List with a non-empty name; the response includes id and name.
- FR2: A client can fetch one List by id and fetch all Lists; no Lists yields an empty collection.
- FR3: A client can rename a List, with the same validation as FR1.
- FR4: A client can delete a List; its Todos are deleted with it.
- FR5: A client can create a Todo with a non-empty title in an existing List; done status defaults to not done.
- FR6: A client can fetch one Todo by id, including id, title, done status and list id.
- FR7: A client can change a Todo's title and/or done status; unspecified fields are unchanged.
- FR8: A client can delete a Todo.
- FR9: A client can fetch all Todos in a given List; an empty List yields an empty collection, a missing List yields not-found.
- FR10: A client can move a Todo to another existing List; title and done status are unchanged.
- FR11: All Lists and Todos survive an application restart.
- FR12: Not-found and validation failures use a consistent status code and body across all endpoints; no client-caused condition yields a 5xx.

### NonFunctional Requirements

- NFR1: Stack is FastAPI, Pydantic and stdlib `sqlite3` only; no new dependencies.
- NFR2: Every FR consequence is covered by an automated test that passes (SM-1).
- NFR3: Requests with non-existent ids never return 5xx (SM-2).
- NFR4: No endpoints beyond what the FRs need (SM-C1).

### Additional Requirements

- No starter template; greenfield package `todo_api/` in `spor/bmad/` per the spine's source tree.
- Layered dependencies api → service → repository → db; only `repository.py` and `db.py` import `sqlite3` (AD-1).
- One connection per request via FastAPI dependency, `PRAGMA foreign_keys = ON`, commit at request end, rollback on error (AD-2).
- Missing rows: repository returns `None`, service raises `NotFoundError`, one handler maps to 404 `{"detail": "<Entity> <id> not found"}`; validation uses FastAPI 422 (AD-3).
- `todos.list_id` is `NOT NULL REFERENCES lists(id) ON DELETE CASCADE` (AD-4).
- `PATCH /todos/{todo_id}` is the single Todo mutation path, including move via `list_id` (AD-5).
- Tables created with `CREATE TABLE IF NOT EXISTS` in `db.init_db` at startup; no migration tool (AD-6).
- `create_app(db_path)`; default from env `TODO_DB_PATH`, fallback `todo.db`; tests use a temp path (AD-7).
- Conventions: status codes 201/200/204/404/422; snake_case JSON; bare arrays ordered by id; Pydantic `ListCreate/ListUpdate/ListRead/TodoCreate/TodoUpdate/TodoRead`.

### UX Design Requirements

None. API-only product.

### FR Coverage Map

- FR1: Epic 1, Story 1.1 - Create List
- FR2: Epic 1, Story 1.1 - Fetch Lists
- FR3: Epic 1, Story 1.4 - Rename List
- FR4: Epic 1, Story 1.4 - Delete List with cascade
- FR5: Epic 1, Story 1.2 - Create Todo
- FR6: Epic 1, Story 1.2 - Fetch Todo
- FR7: Epic 1, Story 1.3 - Update Todo
- FR8: Epic 1, Story 1.3 - Delete Todo
- FR9: Epic 1, Story 1.2 - Todos in a List
- FR10: Epic 1, Story 1.3 - Move Todo
- FR11: Epic 1, Stories 1.1 and 1.2 - Persistence per table
- FR12: Epic 1, all stories - Consistent error responses

## Epic List

### Epic 1: Manage Todos in persistent Lists

A client can organise Todos in named Lists, mark them done, move them between Lists, and remove what it no longer needs, with data that survives restarts and predictable answers for anything that does not exist.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12

## Epic 1: Manage Todos in persistent Lists

A client can organise Todos in named Lists, mark them done, move them between Lists, and remove what it no longer needs, with data that survives restarts and predictable answers for anything that does not exist.

### Story 1.1: Create and fetch Lists

As a client developer,
I want to create Lists and fetch them back, also after a restart,
So that I have somewhere durable to put Todos.

**Implements:** FR1, FR2, FR11, FR12. AD-1, AD-2, AD-3, AD-6, AD-7.

Scope includes the `todo_api/` skeleton (app factory, connection dependency, `NotFoundError` handler) and the `lists` table only.

**Acceptance Criteria:**

**Given** the API is running with an empty database
**When** the client sends `POST /lists` with `{"name": "Groceries"}`
**Then** the response is 201 with `{"id": <int>, "name": "Groceries"}`

**Given** a List exists
**When** the client sends `GET /lists/{list_id}` with its id
**Then** the response is 200 with that List

**Given** Lists "A" and "B" were created in that order
**When** the client sends `GET /lists`
**Then** the response is 200 with a bare array of both, ordered by id ascending
**And** with no Lists the response is 200 with `[]`

**Given** no List has id 999
**When** the client sends `GET /lists/999`
**Then** the response is 404 with `{"detail": "List 999 not found"}`

**Given** a request body with `"name": ""`, `"name": "   "`, or no `name`
**When** the client sends `POST /lists`
**Then** the response is 422 and no List is created

**Given** a List was created with `create_app(db_path)`
**When** a new app is created with the same `db_path`
**Then** `GET /lists/{list_id}` returns the same List unchanged (FR11)

### Story 1.2: Create Todos and read them per List

As a client developer,
I want to add Todos to a List and read them individually or per List,
So that I can render what needs doing.

**Implements:** FR5, FR6, FR9, FR11, FR12. AD-4 (schema), AD-6.

Scope adds the `todos` table with `list_id NOT NULL REFERENCES lists(id) ON DELETE CASCADE`.

**Acceptance Criteria:**

**Given** List 1 exists
**When** the client sends `POST /todos` with `{"title": "Milk", "list_id": 1}`
**Then** the response is 201 with `{"id": <int>, "title": "Milk", "done": false, "list_id": 1}`

**Given** List 1 exists
**When** the client sends `POST /todos` with `{"title": "Bread", "list_id": 1, "done": true}`
**Then** the response is 201 with `"done": true`

**Given** no List has id 999
**When** the client sends `POST /todos` with `{"title": "Milk", "list_id": 999}`
**Then** the response is 404 with `{"detail": "List 999 not found"}`
**And** no Todo is created

**Given** a request body with an empty or whitespace-only `title`, or without `title` or `list_id`
**When** the client sends `POST /todos`
**Then** the response is 422

**Given** a Todo exists
**When** the client sends `GET /todos/{todo_id}`
**Then** the response is 200 with its id, title, done and list_id
**And** `GET /todos/999` for a missing Todo returns 404 with `{"detail": "Todo 999 not found"}`

**Given** List 1 has two Todos and List 2 has one
**When** the client sends `GET /lists/1/todos`
**Then** the response is 200 with only List 1's two Todos, ordered by id ascending

**Given** List 3 exists with no Todos
**When** the client sends `GET /lists/3/todos`
**Then** the response is 200 with `[]`
**And** `GET /lists/999/todos` for a missing List returns 404

**Given** a Todo was created
**When** a new app is created with the same `db_path`
**Then** `GET /todos/{todo_id}` returns the same Todo unchanged (FR11)

### Story 1.3: Update, move and delete Todos

As a client developer,
I want to mark Todos done, rename them, move them between Lists and delete them,
So that the Todo data stays current as work progresses.

**Implements:** FR7, FR8, FR10, FR12. AD-5.

**Acceptance Criteria:**

**Given** a Todo `{"title": "Milk", "done": false}` exists
**When** the client sends `PATCH /todos/{todo_id}` with `{"done": true}`
**Then** the response is 200 with `"done": true` and `"title": "Milk"` unchanged

**Given** a Todo exists
**When** the client sends `PATCH /todos/{todo_id}` with `{"title": "Oat milk"}`
**Then** the response is 200 with the new title and `done` unchanged
**And** `{"title": ""}` returns 422 and the Todo is unchanged

**Given** a Todo in List 1 and List 2 exists
**When** the client sends `PATCH /todos/{todo_id}` with `{"list_id": 2}`
**Then** the response is 200 with `"list_id": 2`, title and done unchanged
**And** the Todo appears in `GET /lists/2/todos` and not in `GET /lists/1/todos`

**Given** a Todo in List 1
**When** the client sends `PATCH /todos/{todo_id}` with `{"list_id": 1}`
**Then** the response is 200 and nothing changes

**Given** a Todo in List 1 and no List has id 999
**When** the client sends `PATCH /todos/{todo_id}` with `{"list_id": 999, "title": "X"}`
**Then** the response is 404 with `{"detail": "List 999 not found"}`
**And** the Todo is unchanged, including its title

**Given** no Todo has id 999
**When** the client sends `PATCH /todos/999` with any valid body
**Then** the response is 404 with `{"detail": "Todo 999 not found"}`

**Given** a Todo exists
**When** the client sends `DELETE /todos/{todo_id}`
**Then** the response is 204 with no body
**And** a later `GET /todos/{todo_id}` returns 404
**And** `DELETE /todos/999` for a missing Todo returns 404

### Story 1.4: Rename and delete Lists

As a client developer,
I want to rename Lists and delete them together with their Todos,
So that I can restructure and clean up.

**Implements:** FR3, FR4, FR12. AD-4.

**Acceptance Criteria:**

**Given** a List "Groceries" exists
**When** the client sends `PATCH /lists/{list_id}` with `{"name": "Food"}`
**Then** the response is 200 with `"name": "Food"`
**And** `{"name": ""}` returns 422 and the name is unchanged
**And** `PATCH /lists/999` for a missing List returns 404 with `{"detail": "List 999 not found"}`

**Given** List 1 has two Todos and List 2 has one
**When** the client sends `DELETE /lists/1`
**Then** the response is 204 with no body
**And** `GET /lists/1` returns 404
**And** `GET /todos/{todo_id}` returns 404 for both of List 1's former Todos
**And** List 2's Todo is still returned by `GET /lists/2/todos`

**Given** no List has id 999
**When** the client sends `DELETE /lists/999`
**Then** the response is 404

**Given** the full test suite
**When** it runs every endpoint with non-existent ids
**Then** no response has a 5xx status (FR12, NFR3)
