# HTTP Contract: Todo Lists API

JSON in, JSON out. Base path is the service root. Every error body is
`{"detail": <string or FastAPI validation array>}`.

## Route table

| # | Method | Path | Purpose | Success | Not-found cases |
| --- | --- | --- | --- | --- | --- |
| R1 | POST | `/lists` | Create a list | 201 | — |
| R2 | GET | `/lists` | All lists, creation order | 200 | — |
| R3 | GET | `/lists/{list_id}` | One list | 200 | list |
| R4 | PATCH | `/lists/{list_id}` | Rename a list | 200 | list |
| R5 | DELETE | `/lists/{list_id}` | Delete a list and its todos | 204 | list |
| R6 | GET | `/lists/{list_id}/todos` | The list's todos | 200 | list |
| R7 | POST | `/lists/{list_id}/todos` | Create a todo in the list | 201 | list |
| R8 | GET | `/lists/{list_id}/todos/{todo_id}` | One todo, membership checked | 200 | list, or todo-not-in-list |
| R9 | GET | `/todos/{todo_id}` | One todo | 200 | todo |
| R10 | PATCH | `/todos/{todo_id}` | Change title and/or done | 200 | todo |
| R11 | DELETE | `/todos/{todo_id}` | Delete a todo | 204 | todo |
| R12 | POST | `/todos/{todo_id}/move` | Move to another list | 200 | todo, or destination list |

Requirement coverage (Constitution Principle IV): create/read/update/delete for
lists is R1–R5, for todos R7/R9/R10/R11; a list's todos is R6; move is R12.
R8 exists for FR-017. FR-018 is met by `list_id` being present on every todo
representation.

## Representations

**List**

```json
{ "id": 1, "name": "Handleliste" }
```

**Todo**

```json
{ "id": 7, "title": "Kjøpe melk", "done": false, "list_id": 1 }
```

## Request bodies

| Route | Body | Rules |
| --- | --- | --- |
| R1 | `{"name": "..."}` | `name` required, trimmed, non-empty |
| R4 | `{"name": "..."}` | `name` required, trimmed, non-empty |
| R7 | `{"title": "...", "done": false}` | `title` required, trimmed, non-empty; `done` optional, defaults false |
| R10 | `{"title": "...", "done": true}` | both optional; omitted fields unchanged; at least one required |
| R12 | `{"list_id": 2}` | required; destination must exist |

## Status codes

| Code | Meaning | When |
| --- | --- | --- |
| 200 | OK | Reads and updates |
| 201 | Created | R1, R7 |
| 204 | No Content | R5, R11 — empty body |
| 404 | Not Found | Any named list or todo does not exist, or a todo is addressed under a list it is not in |
| 422 | Unprocessable Entity | Body fails validation: missing field, empty/whitespace name or title, empty PATCH body, non-integer id in the path |

404 and 422 are deliberately distinct: 404 means "no such thing", 422 means "the
thing you sent is not usable" (FR-014). Neither is ever a 500 (Principle III).

## Not-found message shape

The body names the resource and the identifier that failed, so a client can tell
which of two identifiers in a path was the problem:

```json
{ "detail": "List 99 not found" }
{ "detail": "Todo 42 not found" }
{ "detail": "Todo 7 not found in list 2" }
```

For R12 a missing destination reports the *list*, not the todo, since the todo
was found and the destination was not.

## Worked examples

```http
POST /lists
{"name": "Handleliste"}
→ 201 {"id": 1, "name": "Handleliste"}

POST /lists/1/todos
{"title": "Kjøpe melk"}
→ 201 {"id": 1, "title": "Kjøpe melk", "done": false, "list_id": 1}

PATCH /todos/1
{"done": true}
→ 200 {"id": 1, "title": "Kjøpe melk", "done": true, "list_id": 1}

POST /todos/1/move
{"list_id": 2}
→ 200 {"id": 1, "title": "Kjøpe melk", "done": true, "list_id": 2}

GET /lists/1/todos
→ 200 []

GET /lists/99
→ 404 {"detail": "List 99 not found"}

POST /lists/1/todos
{"title": "   "}
→ 422 (validation error on "title")

DELETE /lists/2
→ 204, and the todo that was in list 2 is gone:
GET /todos/1 → 404 {"detail": "Todo 1 not found"}
```

## Invariants a client may rely on

1. A todo's `list_id` always names an existing list.
2. A todo's `id` does not change when it is moved, renamed or completed.
3. Deleting a list deletes its todos; no todo outlives its list.
4. `GET /lists/{id}/todos` on an existing empty list is `200 []`, never 404 —
   an empty list is a successful answer, not a missing one.
5. Collections come back in creation order.
