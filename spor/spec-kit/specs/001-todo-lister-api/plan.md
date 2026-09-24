# Implementation Plan: TODO-API med lister

**Branch**: `spor/spec-kit` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-todo-lister-api/spec.md`

## Summary

Et HTTP-API over to entiteter — lister og gjøremål — der hvert gjøremål hører
hjemme i nøyaktig én liste. Elleve endepunkter dekker de ti operasjonene i
SC-001. Tilstanden ligger i en SQLite-fil på disk, skrevet gjennom håndskrevet
SQL mot `sqlite3` fra standardbiblioteket.

Den tekniske tilnærmingen hviler på tre valg fra [research.md](./research.md):
fremmednøkler slått på per tilkobling så relasjonen håndheves av databasen og
ikke av påpasselighet (D-001), én tilkobling per forespørsel via en
FastAPI-avhengighet så trådpoolen ikke blir et problem (D-002), og tre
unntakshåndterere som normaliserer *alle* feilsvar til én konvolutt (D-004).
Det siste er det som gjør «finnes ikke» til et normalt svar framfor et
sammenbrudd — kravets egentlige kjerne.

## Technical Context

**Language/Version**: Python 3.12.11 (målt i repoets `.venv`)

**Primary Dependencies**: FastAPI 0.141.1, Pydantic 2.13.5, `sqlite3` fra
standardbiblioteket (SQLite 3.53.4). Ingen nye avhengigheter — grunnloven
prinsipp II.

**Storage**: Én SQLite-fil på disk. Sti fra `TODO_DB_PATH`, standard `todo.db` i
arbeidskatalogen. Skjema opprettes idempotent ved oppstart.

**Testing**: `pytest` 8.3+ med `httpx`/`TestClient`, begge allerede i
`dependency-groups.dev` i repo-roten. Hver test kjører mot sin egen `tmp_path`-fil.

**Target Platform**: Lokal `uvicorn`-prosess, startet med
`make run APP=todo_api.main:app` fra `spor/spec-kit`.

**Project Type**: Web-tjeneste, enkelt prosjekt uten frontend.

**Performance Goals**: Ingen tallfestede mål i spesifikasjonen. Datamengden
antas liten (Assumptions); ingen paginering, ingen indekser utover primærnøkler
og fremmednøkkelen.

**Constraints**: Data må overleve omstart (FR-017). Ingen uhåndterte feil
(FR-015). Én feilform i hele API-et (FR-016). Ingen skriving utenfor
`spor/spec-kit`.

**Scale/Scope**: 2 tabeller, 11 endepunkter, 19 funksjonelle krav. Én prosess,
én skriver, ingen samtidighet utover uvicorns trådpool.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Port | Prinsipp | Før Phase 0 | Etter Phase 1 |
| --- | --- | --- | --- |
| G1 | I. Kravene avgrenser omfanget | PASS | PASS |
| G2 | II. Låst stack | PASS | PASS |
| G3 | III. Varig lagring | PASS | PASS |
| G4 | IV. Fravær er et normalt svar | PASS | PASS |
| G5 | V. Oppførsel verifiseres med tester | PASS | PASS |

**G1 — Omfang**: Ingen autentisering, ingen brukere, ingen paginering, ingen
frister, ingen tagger, ingen mykt slett. Hvert endepunkt i
[contracts/](./contracts/) er sporet til minst ett FR. Det ene tillegget utover
rå CRUD — `POST /todos/{id}/move` — er begrunnet i FR-011 (D-009), ikke i smak.
Etter Phase 1: ingen endepunkter, tabeller eller kolonner uten et FR bak seg.

**G2 — Stack**: `pyproject.toml` i repo-roten røres ikke. Ingen ORM, ingen
migreringsmotor, ingen driver. All SQL er håndskrevet og parameterisert; ingen
verdi interpoleres inn i en setning. Etter Phase 1: `data-model.md` viser rå
DDL, og kolonnenavn i `SET`-klausuler bygges fra en fast hvitliste i koden, ikke
fra klientens nøkler.

**G3 — Varighet**: SQLite-fil på disk, `CREATE TABLE IF NOT EXISTS` ved oppstart,
`PRAGMA foreign_keys = ON` per tilkobling (D-001, målt nødvendig). Ingen
modulglobal dict. Ingen `:memory:` som produksjonslager — heller ikke i testene,
der den ville skjult nettopp det FR-017 måler (D-011).

**G4 — Fravær**: `NotFoundError` → 404 med `resource`-felt, valideringsfeil →
422, begge i samme konvolutt (D-004). Ingen sti der `sqlite3.IntegrityError`
eller et oppslag på `None` kan nå klienten som 500 (D-005). Etter Phase 1: hvert
endepunkt i kontrakten lister sine feilsvar eksplisitt.

**G5 — Tester**: Hvert FR har minst én test; sporingen står i
[quickstart.md](./quickstart.md). Testene bruker `TestClient` mot en app bygget
av `create_app(tmp_path/...)`, så de er uavhengige av rekkefølge og av hverandres
data (D-011).

*Ingen brudd. `Complexity Tracking` er derfor utelatt.*

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-lister-api/
├── plan.md              # Denne filen
├── spec.md              # /speckit-specify
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── http-api.md      # Phase 1
├── checklists/
│   └── requirements.md  # /speckit-specify
└── tasks.md             # /speckit-tasks — ikke laget her
```

### Source Code (spor/spec-kit)

```text
todo_api/
├── __init__.py
├── main.py           # create_app(), app = create_app(), feilhåndterere
├── db.py             # tilkobling, PRAGMA, skjema, get_conn-avhengighet
├── errors.py         # NotFoundError, feilkonvolutt, handlers
├── models.py         # Pydantic: TodoList, Todo, *Create, *Update, MoveRequest
├── repository.py     # all SQL — lists_* og todos_*
└── routers/
    ├── __init__.py
    ├── lists.py      # /lists...
    └── todos.py      # /todos...

tests/
├── __init__.py
├── conftest.py       # client-fixture mot tmp_path
├── test_app.py       # røyktest: oppstart, skjema, foreign_keys-pragma
├── test_lists.py     # FR-001..FR-005
├── test_todos.py     # FR-006..FR-010
├── test_move.py      # FR-011
├── test_errors.py    # FR-012..FR-016
└── test_persistence.py  # FR-017..FR-019
```

**Structure Decision**: Enkelt prosjekt, flat pakke `todo_api/` direkte under
`spor/spec-kit` — ikke `src/`-layout. Grunnen er `make run APP=<modul>:<variabel>`:
uvicorn legger arbeidskatalogen på `sys.path`, så `todo_api.main:app` virker uten
at noe må installeres eller pakkes. Et `src/`-lag ville krevd enten en
pakkeinstallasjon eller `PYTHONPATH`-fikling for en oppgave på denne størrelsen.

Lagdelingen er tre tynne lag: rutene oversetter HTTP til kall, `repository.py`
eier all SQL, `models.py` eier kontrakten. `repository.py` returnerer Pydantic-
modeller, ikke `sqlite3.Row` — grunnloven krever at raddata ikke lekker ut i
rutene. Ingen `services/`-lag: det ville vært et gjennomstikkslag uten egen logikk
på dette omfanget (prinsipp I).
