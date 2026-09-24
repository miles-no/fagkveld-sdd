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
