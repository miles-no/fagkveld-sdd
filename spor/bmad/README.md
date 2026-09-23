# bmad

Oppdraget: [`../../oppgave/krav.md`](../../oppgave/krav.md). Bygg i denne
mappen; de andre sporene løser samme oppgave i sine.

## Før dere starter

For deltakerne, ikke agenten. Fra repo-roten:

```bash
git switch -c spor/bmad
cd spor/bmad
make install
python3 ../../metrics/tokens.py --start-now   # én gang; ny kjøring flytter starten
claude                                        # herfra, ellers måles ikke sesjonen
```

Commit bare `spor/bmad` (inkludert `metrics/`). Branchen merges inn på
`main` til slutt.

`make run APP=<modul>:<variabel>`, `make test` og `make lint` kjøres herfra.

## BMAD

Skillene ligger i `.claude/skills/bmad-*`, konfigurasjonen i `_bmad/`. Alt
BMAD skriver, havner i `_bmad-output/`. Kjør `/clear` mellom stegene;
`/bmad-help` sier hva som er neste.

| Kommando | Gjør |
| --- | --- |
| `/bmad-prd` | PRD fra kravene; gi den `../../oppgave/krav.md` |
| `/bmad-architecture` | tekniske beslutninger |
| `/bmad-create-epics-and-stories` | historier med akseptansekriterier |
| `/bmad-sprint-planning` | sjekker planen, lager `sprint-status.yaml` |
| `/bmad-build` | bygger én historie per kjøring |

Valgfritt etterpå: `/bmad-code-review`, `/bmad-qa-generate-e2e-tests`.

Kortere vei: `/bmad-spec ../../oppgave/krav.md` lager en `SPEC.md` i
`_bmad-output/specs/`, og `/bmad-build <sti til SPEC.md>` bygger fra den.

- `/bmad-build` stopper hvis arbeidskatalogen har ucommittede endringer.
  Stop-hooken skriver `metrics/` etter hvert svar, så det skjer nesten
  alltid. Svar at det er greit, eller commit mellom historiene.
- BMAD snakker engelsk. For norsk: sett `communication_language` og
  `document_output_language` i `_bmad/custom/config.toml`,
  `_bmad/core/config.yaml` og `_bmad/bmm/config.yaml`.
