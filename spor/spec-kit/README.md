# spec-kit

Oppdraget: [`../../oppgave/krav.md`](../../oppgave/krav.md). Bygg i denne
mappen; de andre sporene løser samme oppgave i sine.

## Før dere starter

For deltakerne, ikke agenten. Fra repo-roten:

```bash
git switch -c spor/spec-kit
cd spor/spec-kit
make install
python3 ../../metrics/tokens.py --start-now   # én gang; ny kjøring flytter starten
claude                                        # herfra, ellers måles ikke sesjonen
```

Commit bare `spor/spec-kit` (inkludert `metrics/`). Branchen merges inn på
`main` til slutt.

`make run APP=<modul>:<variabel>`, `make test` og `make lint` kjøres herfra.

## Spec Kit

Kommandoene ligger i `.claude/skills/speckit-*`, maler og skript i
`.specify/`. Hvert steg skriver en fil neste steg leser.

| Kommando | Gjør |
| --- | --- |
| `/speckit-constitution Utled prinsippene fra ../../oppgave/krav.md.` | prosjektets prinsipper |
| `/speckit-specify <oppdraget>` | `spec.md`: hva og hvorfor, uten tekniske valg |
| `/speckit-clarify` | valgfri: opptil fem spørsmål, svarene inn i spec |
| `/speckit-plan` | `plan.md` og designfiler; stacken kommer inn her |
| `/speckit-tasks` | `tasks.md` |
| `/speckit-analyze` | valgfri: sjekker at spec, plan og oppgaver henger sammen |
| `/speckit-implement` | bygger etter `tasks.md` |

- `.specify/memory/constitution.md` er en tom mal og må fylles først. Alle
  senere steg sjekker seg mot den.
- Alt havner i `specs/001-<navn>/`.
- `/speckit-converge` legger det som ikke ble bygget inn som nye oppgaver.
