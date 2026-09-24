# Phase 1: Data Model — TODO-API med lister

**Spec**: [spec.md](./spec.md) | **Beslutninger**: [research.md](./research.md)

## Entiteter

### TodoList (tabell `lists`)

| Felt | Type | Regler | Krav |
| --- | --- | --- | --- |
| `id` | int | Tildeles av databasen, unik, stabil over omstart | FR-001, FR-017 |
| `name` | str | Påkrevd. Trimmes. 1–200 tegn etter trimming | FR-001, FR-014 |

Duplikate navn er tillatt (Assumptions) — ingen unik indeks på `name`.

### Todo (tabell `todos`)

| Felt | Type | Regler | Krav |
| --- | --- | --- | --- |
| `id` | int | Tildeles av databasen, unik, stabil over omstart | FR-006, FR-017 |
| `title` | str | Påkrevd. Trimmes. 1–500 tegn etter trimming | FR-006, FR-014 |
| `done` | bool | Standard `false` ved oppretting | FR-006 |
| `list_id` | int | Påkrevd. Må peke på en eksisterende liste | FR-006, FR-018 |

`done` lagres som `INTEGER` 0/1 — SQLite har ingen boolsk type — og konverteres
til `bool` i grensesnittet mot Pydantic.

Grensene 200 og 500 tegn står ikke i kravene. De er et vanlig inndatavern som
faller inn under FR-014, og er tatt med bevisst framfor å la feltene være
ubegrensede.

## Relasjon

Én liste har null eller flere gjøremål. Ett gjøremål hører til nøyaktig én liste.

Relasjonen håndheves i databasen med en fremmednøkkel og `ON DELETE CASCADE`,
ikke i Python. `PRAGMA foreign_keys = ON` **må** settes på hver tilkobling, ellers
er erklæringen uvirksom (D-001, målt). Det er dette som gjør FR-018 til en
garanti framfor et løfte.

## Skjema

Kjøres idempotent ved oppstart av applikasjonen (D-011).

```sql
CREATE TABLE IF NOT EXISTS lists (
    id   INTEGER PRIMARY KEY,
    name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS todos (
    id      INTEGER PRIMARY KEY,
    title   TEXT    NOT NULL,
    done    INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1)),
    list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_todos_list_id ON todos(list_id);
```

`idx_todos_list_id` er der fordi `GET /lists/{id}/todos` (FR-010) og cascade-
slettingen (FR-005) begge slår opp på den kolonnen. Det er den eneste indeksen
utover primærnøklene.

## Pydantic-modeller

| Modell | Felt | Brukes av |
| --- | --- | --- |
| `TodoListCreate` | `name: str` | `POST /lists` |
| `TodoListUpdate` | `name: str \| None = None` | `PATCH /lists/{id}` |
| `TodoList` | `id, name` | alle listesvar |
| `TodoCreate` | `title: str`, `done: bool = False` | `POST /lists/{id}/todos` |
| `TodoUpdate` | `title: str \| None = None`, `done: bool \| None = None` | `PATCH /todos/{id}` |
| `MoveRequest` | `list_id: int` | `POST /todos/{id}/move` |
| `Todo` | `id, title, done, list_id` | alle gjøremålssvar |

`list_id` finnes ikke i `TodoCreate` — listen kommer fra stien — og ikke i
`TodoUpdate`, fordi flytting er et eget endepunkt (D-009).

### Validering

- `name` og `title` trimmes med en `field_validator(mode="after")` som avviser
  strengen hvis den er tom etter trimming. `min_length` alene ville sluppet
  `"   "` gjennom, som er kanttilfellet «kun-blanke» i spesifikasjonen.
- `*Update`-modellene skiller «ikke sendt» fra «sendt» via `exclude_unset`
  (D-008), ikke via `None`-sjekk.
- Alle modellene settes `model_config = ConfigDict(extra="forbid")` slik at en
  klient som sender `{"titel": "..."}` får 422 framfor en stille ignorering.

## Tilstandsoverganger

`Todo.done` går fritt mellom `false` og `true` i begge retninger (FR-008). Ingen
andre tilstander finnes — statusen er binær (Assumptions).

`Todo.list_id` endres kun av `POST /todos/{id}/move` (FR-011), og kun til en
liste som finnes. Flytting til listen gjøremålet allerede ligger i er en gyldig
operasjon uten effekt.

Sletting er endelig i begge retninger: ingen papirkurv, ingen `deleted_at`
(Assumptions).

## Invarianter

| # | Invariant | Håndheves av |
| --- | --- | --- |
| INV-1 | Ethvert gjøremål peker på en liste som finnes | `NOT NULL` + fremmednøkkel + pragma (D-001) |
| INV-2 | Sletting av en liste etterlater ingen foreldreløse gjøremål | `ON DELETE CASCADE` (verifisert) |
| INV-3 | `title` og `name` er aldri tomme eller kun blanke | Pydantic-validator + `NOT NULL` |
| INV-4 | `done` er alltid 0 eller 1 | `CHECK`-betingelse |
| INV-5 | En feilet operasjon etterlater ingen delvis skrevne data | `with conn:` per skriving (D-010), FR-019 |
