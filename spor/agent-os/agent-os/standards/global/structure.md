# Kodeorganisering

Tre lag, hver sin fil. Avhengigheter peker én vei: `api` → `db` → `models`.

```
app/
  main.py          FastAPI-instans, skjema ved oppstart, ruterne monteres
  db.py            tilkobling, skjema, spørringer — eneste fil med SQL
  models.py        Pydantic-modeller
  dependencies.py  Connection-aliaset rutene henger avhengigheten på
  routes/
    lists.py       APIRouter for /lists
    todos.py       APIRouter for /lists/{id}/todos og /todos/{id}
conftest.py        gjør app-pakken importerbar for pytest
tests/
  conftest.py      klient mot egen database per test
  test_lists.py
  test_todos.py
```

- **SQL bor bare i `db.py`.** Ruter kaller funksjoner, skriver ikke spørringer.
- `db.py` kjenner ikke HTTP. Den returnerer `dict` eller `None`, aldri
  `HTTPException` — ruten oversetter `None` til 404. `dict`, ikke
  `sqlite3.Row`: Row er ingen mapping, og Pydantic kan ikke validere den.
- **Avhengigheten annoteres, ikke defaultes.** `conn: Connection` fra
  `dependencies.py`, ikke `conn = Depends(...)` — det siste er `B008` i ruff.
  Aliaset bor utenfor `db.py` fordi `Depends` er HTTP.
- `find_list` og `find_todo` er oppslagene som kaster 404. De bor i ruteren
  som eier ressursen; `todos.py` importerer `find_list` fra `lists.py`.
- Modellnavn: `TodoList`/`TodoListCreate`/`TodoListUpdate`,
  `Todo`/`TodoCreate`/`TodoUpdate`. `Create` har påkrevde felt, `Update` har
  alt valgfritt og arver `PartialUpdate`.
- Pydantic-modellen for en liste heter `TodoList`, ikke `List` — `list` er
  innebygd og kolliderer i typeannotasjoner.
- Norsk i tekst mot brukeren, engelsk i feltnavn og API-stier.
