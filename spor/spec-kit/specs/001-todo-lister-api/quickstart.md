# Quickstart: validering av TODO-API-et

**Kontrakt**: [contracts/http-api.md](./contracts/http-api.md) | **Modell**: [data-model.md](./data-model.md)

Alt kjøres fra `spor/spec-kit`.

## Forutsetninger

```bash
make install      # allerede gjort i dette repoet; uv sync
```

Python 3.12, FastAPI, Pydantic og `sqlite3` fra standardbiblioteket. Ingen andre
avhengigheter skal dukke opp i `uv.lock` som følge av denne funksjonen.

## Kjøre

```bash
make run APP=todo_api.main:app
```

Starter på `http://127.0.0.1:8000`. Databasefilen blir `todo.db` i
arbeidskatalogen, eller stien i `TODO_DB_PATH`:

```bash
TODO_DB_PATH=/tmp/demo.db make run APP=todo_api.main:app
```

Interaktiv dokumentasjon på `/docs` — den kommer fra FastAPI selv og er nyttig
til å klikke seg gjennom scenariene under.

## Kvalitetsporter

```bash
make test         # hele testsuiten grønn
make lint         # ruff: E, F, I, UP, B — linjelengde 100
```

Begge må være grønne før en oppgave regnes som ferdig (grunnloven, Arbeidsflyt).

---

## Scenario 1 — Samle gjøremål i en liste (User Story 1, P1)

```bash
curl -sX POST localhost:8000/lists \
  -H 'content-type: application/json' -d '{"name":"Handel"}'
# → 201 {"id":1,"name":"Handel"}

curl -sX POST localhost:8000/lists/1/todos \
  -H 'content-type: application/json' -d '{"title":"Kjøpe melk"}'
# → 201 {"id":1,"title":"Kjøpe melk","done":false,"list_id":1}

curl -s localhost:8000/lists/1/todos
# → 200 [{"id":1,"title":"Kjøpe melk","done":false,"list_id":1}]
```

**Forventet**: Listen får en id. Gjøremålet starter som `done: false`. Henting av
listens gjøremål gir nøyaktig det ene.

## Scenario 2 — Holde gjøremålet oppdatert (User Story 2, P2)

```bash
curl -sX PATCH localhost:8000/todos/1 \
  -H 'content-type: application/json' -d '{"done":true}'
# → 200 {"id":1,"title":"Kjøpe melk","done":true,"list_id":1}
```

**Forventet**: `done` er `true`, og `title` er **uendret** selv om den ikke ble
sendt med. Det er kjernen i FR-008 — sender du bare `done`, skal ikke tittelen
forsvinne.

## Scenario 3 — Flytte mellom lister (User Story 3, P3)

```bash
curl -sX POST localhost:8000/lists -H 'content-type: application/json' -d '{"name":"Jobb"}'
# → 201 {"id":2,"name":"Jobb"}

curl -sX POST localhost:8000/todos/1/move \
  -H 'content-type: application/json' -d '{"list_id":2}'
# → 200 {"id":1,"title":"Kjøpe melk","done":true,"list_id":2}

curl -s localhost:8000/lists/1/todos   # → 200 []
curl -s localhost:8000/lists/2/todos   # → 200 [ ... ]
```

**Forventet**: Samme id, samme tittel, samme status — ny liste. Borte fra den
gamle listen, til stede i den nye.

## Scenario 4 — Fravær er et normalt svar (FR-012, FR-013)

```bash
curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/lists/999
# → 404

curl -s localhost:8000/lists/999/todos
# → 404 {"error":{"code":"not_found","resource":"list", ...}}

curl -sX POST localhost:8000/todos/1/move \
  -H 'content-type: application/json' -d '{"list_id":999}'
# → 404 {"error":{"code":"not_found","resource":"list", ...}}

curl -sX POST localhost:8000/lists/1/todos \
  -H 'content-type: application/json' -d '{"title":"   "}'
# → 422 {"error":{"code":"invalid_request","resource":null,"details":[...]}}

curl -s localhost:8000/lists/abc
# → 422 — id på feil form, ikke 404
```

**Forventet**: Ingen 500 noe sted. `resource` skiller «ukjent liste» fra «ukjent
gjøremål». `/lists/999/todos` gir 404, ikke `[]` — en tom liste og en liste som
ikke finnes er to ulike ting. Og gjøremålet som ikke kunne flyttes ligger
fortsatt urørt i listen sin.

## Scenario 5 — Data overlever omstart (FR-017)

```bash
TODO_DB_PATH=/tmp/demo.db make run APP=todo_api.main:app
# opprett en liste og et gjøremål via kallene over, stopp med Ctrl-C

TODO_DB_PATH=/tmp/demo.db make run APP=todo_api.main:app
curl -s localhost:8000/lists
# → 200 — samme lister, samme id-er, samme innhold
```

**Forventet**: Alt er der, med uendrede id-er. Dette er porten mot prinsipp III;
en implementasjon som holder data i minnet klarer alt over, men ikke dette.

## Scenario 6 — Sletting av en liste tar gjøremålene med (FR-005, INV-2)

```bash
curl -sX DELETE localhost:8000/lists/2       # → 204
curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/todos/1   # → 404
curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/lists/1   # → 200
```

**Forventet**: Gjøremålet i den slettede listen er borte — ingen foreldreløse
rader. Den andre listen er urørt. Virker dette *ikke*, er som regel
`PRAGMA foreign_keys = ON` glemt på tilkoblingen (D-001).

---

## Sporing: krav → test

Hvert funksjonelt krav skal ha minst én automatisert test (SC-005).

| Krav | Testfil | Hva den viser |
| --- | --- | --- |
| FR-001–FR-005 | `tests/test_lists.py` | CRUD på lister, cascade ved sletting |
| FR-006–FR-009 | `tests/test_todos.py` | CRUD på gjøremål, delvis PATCH |
| FR-010 | `tests/test_todos.py` | Gjøremål per liste; tom liste gir `[]` |
| FR-011 | `tests/test_move.py` | Flytting, uendret id/tittel/status, flytt til egen liste |
| FR-012, FR-013 | `tests/test_errors.py` | 404 på alle veier, `resource` skiller list/todo |
| FR-014 | `tests/test_errors.py` | Tom/blank tittel, ukjent felt, id på feil form |
| FR-015 | `tests/test_errors.py` | Ingen 500 i noen av feilveiene |
| FR-016 | `tests/test_errors.py` | Samme konvolutt fra både 404 og 422 |
| FR-017 | `tests/test_persistence.py` | Ny app mot samme fil ser samme data |
| FR-018 | `tests/test_app.py` | `PRAGMA foreign_keys` er på — forutsetningen for cascade |
| FR-018 | `tests/test_persistence.py` | Ingen foreldreløse gjøremål via noen vei |
| FR-019 | `tests/test_persistence.py` | Feilet flytting etterlater ingen endring |

Testene bygger appen med `create_app(tmp_path / "test.db")`, så hver test har sin
egen fil og ingen ser de andres data (D-011). En `:memory:`-database ville gjort
FR-017-testen meningsløs.
