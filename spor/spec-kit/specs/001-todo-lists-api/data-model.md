# Data Model: Todo Lists API

Two tables in one SQLite file. Decisions behind the choices are in
[research.md](./research.md) (D1, D2).

## Entity: List

A named container for todos.

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | System-assigned, never reused (D1) |
| `name` | TEXT | NOT NULL, non-empty after trim | Not unique — duplicates allowed per spec |

## Entity: Todo

A single item of work, always inside exactly one list.

| Field | Type | Constraints | Notes |
| --- | --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | System-assigned, stable across a move |
| `title` | TEXT | NOT NULL, non-empty after trim | Not unique |
| `done` | INTEGER | NOT NULL DEFAULT 0, CHECK (done IN (0,1)) | Stored as 0/1, exposed as a boolean |
| `list_id` | INTEGER | NOT NULL, REFERENCES lists(id) ON DELETE CASCADE | The owning list (FR-011, FR-016) |

## Relationship

`List 1 —— 0..* Todo`

- `NOT NULL` on `list_id` makes a todo without a list unrepresentable (FR-011).
- `ON DELETE CASCADE` deletes a list's todos with it (FR-016).
- Both depend on `PRAGMA foreign_keys = ON`, which SQLite leaves **off** by
  default; it is set in the connection factory (D2).

## Schema DDL

```sql
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    title   TEXT    NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_todos_list_id ON todos(list_id);
```

Every statement is `IF NOT EXISTS`, so startup against a fresh file and against
a populated one behave identically (Principle II).

The index serves the two most common reads — a list's todos, and the membership
check in the nested todo read — both of which filter on `list_id`.

## Validation rules

| Rule | Source | Where enforced |
| --- | --- | --- |
| Name and title are trimmed, then must be non-empty | FR-014, edge cases | Pydantic `StringConstraints(strip_whitespace=True, min_length=1)` → 422 (D9) |
| `done` defaults to false on create | FR-005 | Pydantic default, mirrored by the column default |
| An update must change at least one field | FR-008 | Repository rejects an empty `exclude_unset` payload → 422 |
| Referenced list must exist on create and on move | FR-012 | Repository lookup → `NotFoundError` → 404 (D3) |
| A todo read via a list must belong to it | FR-017 | `WHERE id = ? AND list_id = ?` (D6) |

## State transitions

`done` is the only mutable state, and it is freely reversible:

```text
not done ──set done=true──▶ done
not done ◀──set done=false── done
```

Both directions are required (US3 scenarios 1 and 2). There is no terminal state
and no transition guard — a done todo can be edited, moved and undone.

`list_id` changes only via the move operation (D5), and a move preserves `id`,
`title` and `done` (FR-010).

## Ordering

Lists and todos are returned `ORDER BY id`, which under `AUTOINCREMENT` is
creation order (D1). This satisfies the spec's stable-order assumption without
storing a timestamp the brief never asked for.
