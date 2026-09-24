# Standards for TODO-API

Følgende standarder gjelder for dette arbeidet. Innholdet er kopiert
inn slik det så ut da arbeidet var ferdig.

---

## api/routes

# Ruter

Lister og gjøremål er egne ressurser. Nøsting brukes kun der den uttrykker
noe: gjøremål hentes og opprettes under sin liste.

```
POST   /lists                     201  → Liste
GET    /lists                     200  → Liste[]
GET    /lists/{list_id}           200  → Liste
PATCH  /lists/{list_id}           200  → Liste
DELETE /lists/{list_id}           204  → tom kropp

GET    /lists/{list_id}/todos     200  → Gjøremål[]
POST   /lists/{list_id}/todos     201  → Gjøremål

GET    /todos/{todo_id}           200  → Gjøremål
PATCH  /todos/{todo_id}           200  → Gjøremål
DELETE /todos/{todo_id}           204  → tom kropp
```

- Bare disse ti rutene. Ingen `/todos` uten id — gjøremål listes per liste.
- **Flytting er ingen egen rute.** `PATCH /todos/{id}` med `{"list_id": 3}`.
- Id-er i sti, aldri i kropp. `POST /lists/{id}/todos` tar ikke `list_id`.
- Svar er objektet selv, uten konvolutt: `{"id": 1, "name": "Jobb"}`.
- `PATCH` er delvis: felt som utelates, endres ikke. Ikke `PUT`.

---

## api/errors

# Fravær og feil

At noe ikke finnes er et normalt svar, ikke et unntak som velter noe.

```json
404  {"detail": "Liste 3 finnes ikke"}
404  {"detail": "Gjøremål 7 finnes ikke"}
```

- Rutelaget slår opp raden og svarer 404 selv. Ingen `try/except` rundt
  manglende rader, ingen 500 fra en `None` som sniker seg videre.
- Meldingen navngir ressursen og id-en. Aldri bare `"Not found"`.
- `GET /lists/{id}/todos` på en liste som ikke finnes er 404, ikke `[]` —
  en tom liste og en liste som ikke eksisterer er ikke det samme.
- Flytting til en liste som ikke finnes er 404 på målisten, ikke 400.
- `DELETE` på noe som ikke finnes er 404. Ikke stille 204.
- Valideringsfeil (tom tittel, feil type) er FastAPIs egen 422. Ikke rør.

---

## database/sqlite

# SQLite

`sqlite3` fra standardbiblioteket. Ingen ORM, ingen ny avhengighet.

- **Fil på disk**, aldri `:memory:` i drift — data skal overleve omstart.
  Stien er én konstant, overstyrbar med miljøvariabel så testene får sin egen.
- `PRAGMA foreign_keys = ON` på **hver** tilkobling. SQLite har den av som
  standard, og uten den er `list_id` bare et tall.
- `row_factory = sqlite3.Row`, så rader leses med kolonnenavn. Rader
  konverteres til `dict` før de forlater `db.py` — Pydantic validerer
  mappinger, og `sqlite3.Row` er ikke en.
- Skjemaet opprettes med `CREATE TABLE IF NOT EXISTS` ved oppstart.
- `ON DELETE CASCADE` på `todos.list_id`: sletter man en liste, forsvinner
  gjøremålene i den. Databasen håndhever det, ikke rutelaget.
- **Alltid parameterisert SQL** (`?`). Kolonnenavn kan ikke bindes, så de
  sjekkes mot en hviteliste før de settes inn i en UPDATE.
- `INSERT`/`UPDATE` bruker `RETURNING`, så den endrede raden hentes uten
  et ekstra oppslag.
- Én tilkobling per forespørsel, lukkes etterpå. Skriv i transaksjon.

```sql
CREATE TABLE IF NOT EXISTS lists (
  id   INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS todos (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  title   TEXT NOT NULL,
  done    INTEGER NOT NULL DEFAULT 0,
  list_id INTEGER NOT NULL REFERENCES lists(id) ON DELETE CASCADE
);
```

`done` lagres som 0/1 og eksponeres som `bool` gjennom Pydantic.

---

## global/structure

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

---

## testing/api-tests

# Tester

pytest + FastAPIs `TestClient`. Kjøres med `make test` fra `spor/agent-os/`.

- **Hver test får sin egen database.** En fixture peker databasestien mot
  `tmp_path` og overstyrer avhengigheten. Tester deler aldri tilstand.
- Test gjennom HTTP, ikke mot `db.py` direkte. Det er API-et som er produktet.
- **Hvert endepunkt testes både når raden finnes og når den ikke gjør det.**
  404-tilfellet er et krav, ikke en ekstra.
- Egne tester for: flytting mellom lister, at sletting av en liste tar
  gjøremålene med seg, og at data overlever at appen startes på nytt.
- Sjekk statuskode og kropp. `assert r.status_code == 404` alene er for lite.
- Navn sier hva som skjer: `test_henter_gjøremål_i_liste`,
  `test_flytt_til_liste_som_ikke_finnes_gir_404`.

