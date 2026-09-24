# fri

Oppdraget: [`../../oppgave/krav.md`](../../oppgave/krav.md). Bygg i denne
mappen; de andre sporene løser samme oppgave i sine.

## Før dere starter

For deltakerne, ikke agenten. Fra repo-roten:

```bash
git switch -c spor/fri
cd spor/fri
make install
python3 ../../metrics/tokens.py --start-now   # én gang; ny kjøring flytter starten
claude                                        # herfra, ellers måles ikke sesjonen
```

Commit bare `spor/fri` (inkludert `metrics/`). Branchen merges inn på
`main` til slutt.

`make run APP=<modul>:<variabel>`, `make test` og `make lint` kjøres herfra.

## API

`make run APP=todo_api.app:app`. Data lagres i `todo.db` (overstyr med `TODO_DB`).

| Metode | Sti | |
|---|---|---|
| GET/POST | `/lists` | alle lister / ny liste `{name}` |
| GET/PATCH/DELETE | `/lists/{id}` | sletting tar med gjøremålene |
| GET | `/lists/{id}/todos` | gjøremål i lista |
| GET/POST | `/todos` | alle / nytt `{title, list_id, done?}` |
| GET/PATCH/DELETE | `/todos/{id}` | PATCH `{title?, done?, list_id?}`; `list_id` flytter |

Ukjent id gir `404` med `{"detail": "... finnes ikke"}`; ugyldig input gir `422`.
