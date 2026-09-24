# TODO-API i `spor/agent-os`

## Context

Oppdraget i `oppgave/krav.md` ber om et API for gjøremål og lister, bygget fra
bunnen av. Sporet er greenfield — før denne planen fantes det ingen kode, bare
Agent OS-kommandoene.

Flyten fra `README.md` er allerede kjørt for steg 1 og 2:

- `agent-os/product/` — mission, roadmap, tech-stack er skrevet.
- `agent-os/standards/` — fem standarder utledet fra kravene, indeksert i
  `index.yml`: `api/routes`, `api/errors`, `database/sqlite`,
  `global/structure`, `testing/api-tests`.

Denne planen er steg 3, `/shape-spec`. Utfallet er et kjørende API som dekker
alt kravene ber om, med tester, og en spec som forklarer hvorfor det ser slik ut.

**Rammer fra kravene:** FastAPI, Pydantic og `sqlite3` fra standardbiblioteket.
Ingen nye avhengigheter. Data skal overleve omstart.

**Valgt API-form** (bekreftet av bruker — hybrid, nøstet der nøsting betyr noe):

```
POST   /lists                     201    GET    /lists/{list_id}/todos   200
GET    /lists                     200    POST   /lists/{list_id}/todos   201
GET    /lists/{list_id}           200    GET    /todos/{todo_id}         200
PATCH  /lists/{list_id}           200    PATCH  /todos/{todo_id}         200
DELETE /lists/{list_id}           204    DELETE /todos/{todo_id}         204
```

Flytting er ingen egen rute: `PATCH /todos/{id}` med `{"list_id": 3}`.

---

## Task 1: Lagre spec-dokumentasjon

Opprett `agent-os/specs/2026-09-24-1616-todo-api/` med:

- **`plan.md`** — denne planen.
- **`shape.md`** — omfang, beslutninger (API-form, flytting som PATCH, 404 som
  normaltilfelle), og at det ikke finnes referansekode.
- **`standards.md`** — fullt innhold av de fem standardene som gjelder.
- **`references.md`** — «ingen referanseimplementasjon; sporet er greenfield»,
  med peker til `../../oppgave/krav.md` som eneste kilde.

Ingen `visuals/` — API uten grensesnitt, ingen mockups finnes.

## Task 2: Datalag — `app/db.py`

Eneste fil med SQL, kjenner ikke HTTP. Returnerer `sqlite3.Row` eller `None`,
aldri `HTTPException`.

- `database_path()` leser `TODO_DB_PATH` fra miljøet, faller tilbake på
  `todo.db` i arbeidsmappen. Leses ved hvert kall, så testene kan peke den mot
  `tmp_path` uten å overstyre avhengigheter.
- `connect()` setter `row_factory = sqlite3.Row` og `PRAGMA foreign_keys = ON`
  på hver tilkobling — SQLite har fremmednøkler av som standard.
- `create_schema()` kjører `CREATE TABLE IF NOT EXISTS` for `lists` og `todos`.
  `todos.list_id` er `NOT NULL REFERENCES lists(id) ON DELETE CASCADE`, så
  sletting av en liste tar gjøremålene med seg i databasen, ikke i rutelaget.
- `get_connection()` er FastAPI-avhengigheten: åpner, `yield`, `commit()`,
  `close()` i `finally`.
- Spørrefunksjoner, alle parameteriserte med `?`, alle med `conn` som første
  argument: `create_list`, `all_lists`, `get_list`, `update_list`,
  `delete_list`, `create_todo`, `get_todo`, `todos_in_list`, `update_todo`,
  `delete_todo`.

`done` lagres som `INTEGER` 0/1.

## Task 3: Modeller — `app/models.py`

Pydantic v2. `TodoList`, ikke `List` — `list` kolliderer i typeannotasjoner.

- `TodoListCreate` (`name`, `min_length=1`), `TodoListUpdate`
  (`name: str | None = None`), `TodoList` (`id`, `name`).
- `TodoCreate` (`title` påkrevd, `done: bool = False`), `TodoUpdate`
  (`title`, `done`, `list_id` — alle valgfrie), `Todo` (`id`, `title`, `done`,
  `list_id`).

`Update`-modellene leses med `model_dump(exclude_unset=True)` slik at et utelatt
felt er noe annet enn et felt satt til `null`. Det er dette som gjør `PATCH`
delvis. Tom kropp på `PATCH` returnerer raden uendret.

## Task 4: Ruter — `app/routes/lists.py` og `app/routes/todos.py`

To `APIRouter`. Rutene slår opp raden, og oversetter `None` til
`HTTPException(404, "Liste 3 finnes ikke")` / `"Gjøremål 7 finnes ikke"` — med
id i meldingen, aldri bare «Not found».

Tilfellene som må treffes riktig:

- `GET /lists/{id}/todos` på en liste som ikke finnes → **404**, ikke `[]`.
  En tom liste og en liste som ikke eksisterer er ikke det samme.
- `POST /lists/{id}/todos` på en liste som ikke finnes → 404. `list_id` kommer
  fra stien, aldri fra kroppen.
- `PATCH /todos/{id}` med `list_id` → sjekk at målisten finnes før flytting,
  ellers 404 på målisten. Ikke 400, og ikke en fremmednøkkelfeil som blir 500.
- `DELETE` på noe som ikke finnes → 404, ikke stille 204.
- Valideringsfeil (tom tittel, feil type) → FastAPIs egen 422, urørt.

## Task 5: Applikasjon — `app/main.py`

`FastAPI`-instans med `lifespan` som kaller `create_schema()` ved oppstart, og
som monterer begge ruterne. Kjøres med `make run APP=app.main:app` fra
`spor/agent-os/`.

## Task 6: Tester — `tests/`

pytest + `fastapi.testclient.TestClient` (httpx ligger allerede i dev-gruppen).

- `conftest.py`: fixture som setter `TODO_DB_PATH` til `tmp_path` med
  `monkeypatch`, og gir en `TestClient` brukt som kontekstmanager slik at
  `lifespan` kjører og skjemaet opprettes. Hver test får sin egen database.
- `test_lists.py` og `test_todos.py`: hvert endepunkt testet både når raden
  finnes og når den ikke gjør det. Både statuskode og kropp sjekkes.
- Egne tester for de fire som faktisk kan gå galt:
  flytting mellom lister; flytting til en liste som ikke finnes;
  at sletting av en liste tar gjøremålene med seg (cascade);
  at data overlever omstart — ny `TestClient` mot samme fil, raden er der.

## Task 7: Verifisering

Fra `spor/agent-os/`:

```bash
make test    # alle tester grønne
make lint    # ruff, linjelengde 100, regler E/F/I/UP/B
```

Deretter en røyktest mot en faktisk kjørende app — start `make run
APP=app.main:app`, opprett en liste, legg et gjøremål i den, flytt det til en
annen liste, hent `/lists/{id}/todos` for begge, og be om en id som ikke finnes
for å se 404-kroppen. Stopp appen, start den igjen, og hent listen på nytt for
å bekrefte at data overlevde. Rydd opp `todo.db` etterpå (`*.db` er allerede i
`.gitignore`, så den committes ikke).

Til slutt: `git add spor/agent-os` og commit på `spor/agent-os`-branchen, med
`metrics/` inkludert.
