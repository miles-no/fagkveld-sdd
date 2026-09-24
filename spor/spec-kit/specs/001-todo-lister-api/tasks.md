---

description: "Task list for TODO-API med lister"
---

# Tasks: TODO-API med lister

**Input**: Design documents from `specs/001-todo-lister-api/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/http-api.md](./contracts/http-api.md)

**Tests**: Testoppgaver er **med**. Grunnloven prinsipp V gjør dem obligatoriske:
«Hvert krav i spesifikasjonen MÅ ha minst én automatisert test.» De skrives før
implementasjonen i hver fase og skal feile først.

**Organization**: Oppgavene er gruppert per brukerhistorie, slik at hver historie
kan bygges og verifiseres for seg.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Kan kjøres parallelt (ulike filer, ingen avhengighet)
- **[Story]**: Hvilken brukerhistorie oppgaven hører til (US1–US4)
- Alle stier er relative til `spor/spec-kit/`

## Path Conventions

Flat pakke `todo_api/` med `tests/` ved siden av, direkte under `spor/spec-kit`
— ikke `src/`-layout. Se «Structure Decision» i [plan.md](./plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Pakkeskjelett og verktøykjede på plass

- [X] T001 Opprett pakkeskjelettet: `todo_api/__init__.py`, `todo_api/routers/__init__.py`, `tests/__init__.py` (tomme filer)
- [X] T002 [P] Opprett `.gitignore` i `spor/spec-kit/` med `todo.db`, `*.db`, `__pycache__/`, `.pytest_cache/` — databasefilen skal ikke committes
- [X] T003 [P] Verifiser verktøykjeden: `make install`, `make lint` og `make test` kjører uten feil på tomt tre (`make test` returnerer 5 = ingen tester, og Makefile godtar det)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lagring, feilhåndtering, modeller og app-fabrikk — alt som alle
fire historiene hviler på

**⚠️ CRITICAL**: Ingen brukerhistorie kan begynne før denne fasen er ferdig

- [X] T004 [P] Implementer `todo_api/db.py`: DDL-konstant med skjemaet fra [data-model.md](./data-model.md) (`lists`, `todos` med `done INTEGER NOT NULL DEFAULT 0 CHECK (done IN (0, 1))` og `list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE`, samt `idx_todos_list_id`), alt med `IF NOT EXISTS`; `connect(path)` som setter `row_factory = sqlite3.Row` og **`PRAGMA foreign_keys = ON`** på hver tilkobling (D-001 — uten dette er `ON DELETE CASCADE` uvirksom); `init_schema(path)`; og `get_conn`-avhengighet som yielder en tilkobling per forespørsel og lukker den i `finally` (D-002)
- [X] T005 [P] Implementer `todo_api/errors.py`: `NotFoundError(resource, identifier)`; feilkonvolutten `{"error": {"code", "resource", "message", "details"}}` fra [contracts/http-api.md](./contracts/http-api.md); og tre håndterere — `NotFoundError` → 404 med `code="not_found"`, `RequestValidationError` → 422 med `code="invalid_request"` og feltfeil i `details`, og `starlette.exceptions.HTTPException` → egen statuskode i samme konvolutt. **Håndtereren må registreres på Starlette-klassen, ikke på `fastapi.HTTPException`**: oppslaget av håndterere går gjennom MRO-en til unntaket som faktisk kastes, og `fastapi.HTTPException` er en *subklasse*. Registrert på subklassen slipper ukjent rute (404) og feil metode (405) forbi til Starlettes standardsvar `{"detail": "Not Found"}` — en annen kroppsform enn resten av API-et, som er brudd på FR-016 og grunnloven prinsipp IV (D-004, FR-016)
- [X] T006 [P] Implementer `todo_api/models.py`: `TodoListCreate`, `TodoListUpdate`, `TodoList`, `TodoCreate`, `TodoUpdate`, `MoveRequest`, `Todo` per tabellen i [data-model.md](./data-model.md). Alle får `model_config = ConfigDict(extra="forbid")`. `name`: påkrevd, trimmes, «1–200 tegn etter trimming». `title`: påkrevd, trimmes, «1–500 tegn etter trimming». Trimming og tomhetssjekk gjøres i en `field_validator(mode="after")` — `min_length` alene slipper `"   "` gjennom. `done: bool` med standard `False` i `TodoCreate`. `TodoUpdate`-feltene har `None` som standard og leses med `exclude_unset` (D-008)
- [X] T007 [P] Opprett tomme rutere: `todo_api/routers/lists.py` og `todo_api/routers/todos.py`, hver med `router = APIRouter(tags=[...])` og ingen endepunkter ennå. Begge filene fylles av historiefasene
- [X] T008 Implementer `todo_api/main.py`: `create_app(db_path=None)` som leser `TODO_DB_PATH` med `todo.db` som standard, kaller `init_schema` ved oppstart, legger stien på `app.state`, registrerer de tre håndtererne fra T005 og begge rutere fra T007; deretter `app = create_app()` på modulnivå slik `make run APP=todo_api.main:app` krever (D-011)
- [X] T009 Implementer hjelperne i `todo_api/repository.py`: `_to_list(row) -> TodoList` og `_to_todo(row) -> Todo` (konverterer `done` fra `INTEGER` til `bool`), samt `require_list(conn, list_id)` som kaster `NotFoundError("list", id)` hvis listen ikke finnes (D-005). Grunnloven krever at `sqlite3.Row` ikke lekker ut i rutene
- [X] T010 Opprett `tests/conftest.py`: fixture `db_path` som gir `tmp_path / "test.db"`, og fixture `client` som gir `TestClient(create_app(db_path))`. Hver test får sin egen fil — ingen `:memory:`, den ville gjort FR-017-testen meningsløs og gitt hver forespørsel sin egen tomme base (D-002 + D-011)
- [X] T011 Skriv røyktest i `tests/test_app.py`: appen bygges og svarer på `/docs`; `lists` og `todos` finnes i `sqlite_master` etter oppstart; og `PRAGMA foreign_keys` er `1` på en tilkobling fra `connect()` — sistnevnte er den enkeltsjekken som fanger den vanligste feilen i denne oppgaven

**Checkpoint**: Appen starter, skjemaet finnes, feilkonvolutten er på plass —
historiene kan begynne

---

## Phase 3: User Story 1 - Samle gjøremål i en liste (Priority: P1) 🎯 MVP

**Goal**: Opprette en liste, legge et gjøremål i den, og hente ut gjøremålene som
ligger i nettopp den listen. Dekker FR-001, FR-006 og FR-010.

**Independent Test**: Opprett en liste, opprett ett gjøremål i den, hent listens
gjøremål — svaret inneholder gjøremålet og ingenting annet.

### Tests for User Story 1 ⚠️

> Skriv disse først og se dem feile før implementasjonen.

- [X] T012 [P] [US1] Skriv `tests/test_lists.py`: `POST /lists` gir 201 med `id` og `name`; to lister med samme navn er tillatt; tomt og kun-blankt navn gir 422
- [X] T013 [P] [US1] Skriv `tests/test_todos.py`: `POST /lists/{id}/todos` gir 201 med `done: false` som standard og riktig `list_id`; `GET /lists/{id}/todos` gir nøyaktig den listens gjøremål sortert på `id`; en liste uten gjøremål gir `[]`; **en liste som ikke finnes gir 404, ikke `[]`** — og oppretting i en ukjent liste gir 404 med `resource: "list"`, ikke en 500 fra fremmednøkkelen

### Implementation for User Story 1

- [X] T014 [US1] Implementer `create_list(conn, data)` i `todo_api/repository.py` med `INSERT INTO lists(name) VALUES(?) RETURNING id, name` inne i `with conn:` (D-006, D-010)
- [X] T015 [US1] Implementer `create_todo(conn, list_id, data)` og `todos_for_list(conn, list_id)` i `todo_api/repository.py`. Begge kaller `require_list` først (D-005), og `create_todo` pakker innsettingen i `with conn:`. Merk at FR-019 holder fordi operasjonen har **én** skriving — ikke fordi sjekken og skrivingen deler transaksjon; med `isolation_level=''` kjører `SELECT`-en utenfor transaksjonen, som først åpnes ved `INSERT`. `todos_for_list` sorterer på `id ASC`
- [X] T016 [US1] Implementer `POST /lists` → 201 i `todo_api/routers/lists.py`
- [X] T017 [US1] Implementer `POST /lists/{list_id}/todos` → 201 og `GET /lists/{list_id}/todos` → 200 i `todo_api/routers/todos.py` (listescopede gjøremålsruter bor sammen med de andre gjøremålsrutene, ikke i `lists.py`)

**Checkpoint**: MVP. Man kan opprette lister, legge gjøremål i dem og hente dem
ut per liste — med korrekt 404 på ukjent liste.

---

## Phase 4: User Story 2 - Holde gjøremål oppdatert (Priority: P2)

**Goal**: Hente, endre og slette ett enkelt gjøremål. Dekker FR-007, FR-008,
FR-009.

**Independent Test**: Opprett ett gjøremål, sett `done: true`, hent det igjen og
se ny status, slett det og se at det er borte — mens listen består.

### Tests for User Story 2 ⚠️

- [X] T018 [US2] Utvid `tests/test_todos.py`: `GET /todos/{id}` gir tittel, status og `list_id`; `PATCH` med bare `done` lar `title` stå **uendret** og omvendt; tom kropp `{}` gir gjøremålet uendret tilbake med 200; `DELETE` gir 204 og listen består; andre `DELETE` gir 404; `PATCH` med `list_id` i kroppen gir 422 (flytting er et eget endepunkt)

### Implementation for User Story 2

- [X] T019 [US2] Implementer `get_todo(conn, todo_id)`, `update_todo(conn, todo_id, data)` og `delete_todo(conn, todo_id)` i `todo_api/repository.py`. `update_todo` bygger `SET`-delen fra `model_dump(exclude_unset=True)` mot en **fast hvitliste** av kolonnenavn (`title`, `done`) — aldri fra klientens nøkler (grunnloven G2); tomt sett felt betyr ingen `UPDATE`, bare et oppslag. `delete_todo` bruker `cursor.rowcount == 0` → `NotFoundError("todo", id)` uten `SELECT` først (D-007)
- [X] T020 [US2] Implementer `GET /todos/{todo_id}` → 200, `PATCH /todos/{todo_id}` → 200 og `DELETE /todos/{todo_id}` → 204 i `todo_api/routers/todos.py`

**Checkpoint**: Gjøremål kan leve et helt liv — opprettes, endres, krysses av og
slettes.

---

## Phase 5: User Story 3 - Flytte et gjøremål mellom lister (Priority: P3)

**Goal**: Flytte et gjøremål fra én liste til en annen. Dekker FR-011.

**Independent Test**: To lister, ett gjøremål i den første, flytt til den andre —
det dukker opp i den andre og er borte fra den første, med id, tittel og status
uendret.

### Tests for User Story 3 ⚠️

- [X] T021 [US3] Skriv `tests/test_move.py`: flytting bevarer `id`, `title` og `done`; gjøremålet forsvinner fra kildelisten og dukker opp i mållisten; flytting til listen det allerede ligger i lykkes uten effekt; **ukjent gjøremål gir 404 med `resource: "todo"`, ukjent målliste gir 404 med `resource: "list"`** — de to skilles i samme endepunkt (FR-013); og etter en feilet flytting ligger gjøremålet urørt i den opprinnelige listen (FR-019)

### Implementation for User Story 3

- [X] T022 [US3] Implementer `move_todo(conn, todo_id, list_id)` i `todo_api/repository.py`: sjekk at gjøremålet finnes (`NotFoundError("todo", …)`), kall `require_list` for mållisten (`NotFoundError("list", …)`), og `UPDATE todos SET list_id = ? WHERE id = ? RETURNING …` inne i `with conn:`. Rekkefølgen på de to sjekkene er kontraktfestet: gjøremålet først. Som i T015 hviler FR-019 på at det er én skriving, ikke på at sjekkene deler transaksjon med den
- [X] T023 [US3] Implementer `POST /todos/{todo_id}/move` → 200 i `todo_api/routers/todos.py`

**Checkpoint**: Alle tre kjernehistoriene virker. Alt i kravene bortsett fra
listeforvaltningen er dekket.

---

## Phase 6: User Story 4 - Forvalte listene (Priority: P4)

**Goal**: Oversikt over lister, hente én, gi nytt navn, og slette. Dekker FR-002,
FR-003, FR-004, FR-005.

**Independent Test**: Opprett to lister, hent oversikten og se begge, gi den ene
nytt navn, slett den andre, hent oversikten igjen.

### Tests for User Story 4 ⚠️

- [X] T024 [US4] Utvid `tests/test_lists.py`: `GET /lists` gir alle sortert på `id`, og `[]` når ingen finnes; `GET /lists/{id}` gir 404 på ukjent id; `PATCH` endrer navnet og lar listens gjøremål være i fred; tom kropp `{}` gir listen uendret; **`DELETE` av en liste med gjøremål sletter gjøremålene med den (INV-2) og lar andre listers gjøremål være urørt**; andre `DELETE` gir 404

### Implementation for User Story 4

- [X] T025 [US4] Implementer `all_lists(conn)` (sortert på `id ASC`), `get_list(conn, list_id)`, `update_list(conn, list_id, data)` og `delete_list(conn, list_id)` i `todo_api/repository.py`. `update_list` bruker samme hvitliste-mønster som T019; `delete_list` bruker `rowcount` som T019 og hviler på `ON DELETE CASCADE` framfor å slette gjøremål manuelt
- [X] T026 [US4] Implementer `GET /lists` → 200, `GET /lists/{list_id}` → 200, `PATCH /lists/{list_id}` → 200 og `DELETE /lists/{list_id}` → 204 i `todo_api/routers/lists.py`

**Checkpoint**: Alle 11 endepunkter i kontrakten finnes. Alle 19 funksjonelle
krav er implementert.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: De tverrgående kravene — feilform, varighet, integritet — og
portene grunnloven krever

- [X] T027 [P] Skriv `tests/test_errors.py` (FR-012–FR-016): samme konvolutt fra både 404 og 422, verifisert felt for felt; `resource` skiller `list` fra `todo`; `/lists/abc` gir **422, ikke 404** (id på feil form er ugyldig inndata); ukjent felt i kroppen gir 422 (`extra="forbid"`); en sveip over alle 11 endepunkter med ugyldige og ikke-eksisterende id-er der **ingen** svarer 5xx (FR-015); og — kritisk for FR-016 — at `GET /finnes-ikke` (404 fra ruteren) og `POST /todos/1` (405, feil metode) svarer i **samme konvolutt** som alt annet. Det er rammeverkets egne feilsvar, og de er den letteste veien til to ulike kroppsformer i samme API
- [X] T028 [P] Skriv `tests/test_persistence.py` (FR-017–FR-019): bygg en app mot en fil, skriv data, kast appen, bygg en ny app mot **samme** fil og se samme lister og gjøremål med samme id-er; ingen vei — oppretting, flytting eller listesletting — etterlater et gjøremål med `list_id` som ikke finnes (FR-018, sjekk direkte i basen); og en feilet flytting etterlater ingen delvis endring (FR-019)
- [X] T029 Kjør `make lint` fra `spor/spec-kit` og rett alt ruff flagger (`E`, `F`, `I`, `UP`, `B`, linjelengde 100)
- [X] T030 Kjør `make test` og bekreft at hele suiten er grønn
- [X] T031 Gå gjennom de seks scenariene i [quickstart.md](./quickstart.md) mot en kjørende server (`make run APP=todo_api.main:app`), inkludert omstartsscenariet med `TODO_DB_PATH`
- [X] T032 Grunnlovssjekk før ferdig: bekreft at `pyproject.toml` og `uv.lock` i repo-roten er uendret (prinsipp II), at ingen filer utenfor `spor/spec-kit` er rørt, og at sporingstabellen «krav → test» i [quickstart.md](./quickstart.md) stemmer med de faktiske testene (SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Ingen avhengigheter
- **Foundational (Phase 2)**: Krever Phase 1 — **blokkerer alle historier**
- **User Stories (Phase 3–6)**: Krever Phase 2
- **Polish (Phase 7)**: Krever at alle historiene er ferdige — T027 og T028
  sveiper over endepunkter fra alle fire

### User Story Dependencies

- **US1 (P1)**: Ingen avhengigheter utover Phase 2. Dette er MVP-et
- **US2 (P2)**: Uavhengig av US1 i kode, men testene trenger et gjøremål, som
  opprettes via US1s endepunkt. Bygg US1 først
- **US3 (P3)**: Samme — trenger US1s oppretting for å ha noe å flytte
- **US4 (P4)**: Uavhengig. Cascade-testen i T024 trenger US1s
  gjøremålsoppretting for å være meningsfull

Ingen av historiene avhenger av en annens *implementasjon*; avhengighetene er at
testene trenger data som bare US1 kan lage.

### Within Each User Story

- Testene skrives først og skal feile
- `repository.py` før `routers/` — ruten kaller funksjonen
- Historien ferdig og grønn før neste prioritet

### Parallel Opportunities

- **Phase 1**: T002 og T003 parallelt
- **Phase 2**: T004, T005, T006 og T007 parallelt — fire ulike filer uten
  avhengigheter. Deretter T008 → T009 → T010 → T011 i rekkefølge
- **Phase 3**: T012 og T013 parallelt (ulike testfiler)
- **Phase 4–6**: Ingen `[P]` innenfor fasene. Alle implementasjonsoppgavene
  treffer `todo_api/repository.py` eller en ruterfil som allerede er i bruk, og
  to samtidige skrivinger til samme fil er nettopp det `[P]` ikke skal bety
- **Phase 7**: T027 og T028 parallelt (ulike testfiler); T029–T032 sekvensielt

**Ærlig om parallellitet på tvers av historier**: malen foreslår at historier kan
bygges samtidig av flere. Her går det ikke helt. `repository.py`,
`routers/todos.py` og `routers/lists.py` deles av flere historier, så samtidig
arbeid ville kollidert i de filene. Det er en følge av at oppgaven er liten nok
til at en filsplitt per historie ville vært kunstig.

---

## Parallel Example: Phase 2

```bash
# Fire uavhengige filer, ingen felles avhengigheter:
Task: "Implementer todo_api/db.py — skjema, connect(), PRAGMA, get_conn"
Task: "Implementer todo_api/errors.py — NotFoundError, konvolutt, tre håndterere"
Task: "Implementer todo_api/models.py — sju Pydantic-modeller med validatorer"
Task: "Opprett tomme rutere i todo_api/routers/lists.py og todos.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup
2. Phase 2: Foundational — blokkerer alt annet
3. Phase 3: US1
4. **STOPP og VALIDER**: opprett liste → opprett gjøremål → hent listens
   gjøremål. Sjekk at ukjent liste gir 404, ikke `[]`
5. Dette er et brukbart API i seg selv

### Incremental Delivery

1. Setup + Foundational → appen starter, skjemaet finnes
2. + US1 → **MVP**: gjøremål kan samles i lister
3. + US2 → gjøremål kan endres, krysses av og slettes
4. + US3 → gjøremål kan flyttes mellom lister
5. + US4 → listene kan forvaltes fullt ut
6. + Phase 7 → feilform, varighet og integritet verifisert; portene grønne

Hvert steg legger til verdi uten å bryte det forrige.

---

## Notes

- `[P]` = ulike filer, ingen avhengigheter
- Testene skrives før implementasjonen i hver fase og skal feile først
  (grunnloven prinsipp V)
- Commit etter hver oppgave eller logiske gruppe
- Ved hvert checkpoint kan historien valideres for seg
- Den vanligste feilen i denne oppgaven er å glemme
  `PRAGMA foreign_keys = ON` på tilkoblingen. Da virker alt bortsett fra
  cascade-sletting — og det oppdages først i T024. T011 er der for å fange det
  med én gang
