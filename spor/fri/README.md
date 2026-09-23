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
