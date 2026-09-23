# bmad

Applikasjonen bygges i denne mappen.

Oppdraget står i [`../../oppgave/krav.md`](../../oppgave/krav.md).

Hold deg i denne mappen. De andre sporene løser samme oppgave.

Sesjonen må startes her: målingen teller etter hvor sesjonen ble startet,
så en sesjon startet fra repo-roten måles ikke.

`make install`, `make run APP=<modul>:<variabel>`, `make test` og
`make lint` kjøres herfra.

## Oppstart med BMAD

BMAD (versjon 6) er installert i `_bmad/` (konfigurasjon og skript) og
`.claude/skills/bmad-*` (skills). Alt BMAD produserer havner i
`_bmad-output/`: planleggingsdokumenter i `planning-artifacts/`,
implementeringsspesifikasjoner i `implementation-artifacts/`.

BMAD jobber med **roller**: analytiker (Mary), produkteier (John),
arkitekt (Winston), UX (Sally) og utvikler (Amelia). Hver fase har sin
skill, og fasene bygger på hverandre.

### Usikker på hva som er neste steg?

```
/bmad-help
```

Den ser hva som finnes i `_bmad-output/` og anbefaler neste skill. BMAD
anbefaler **ny kontekst for hvert steg** — kjør `/clear` mellom dem.

### Standardløpet

De fire første stegene er planlegging, det siste er bygging.

1. **Krav (PRD)** — `/bmad-prd`
   Gi den [`../../oppgave/krav.md`](../../oppgave/krav.md) som
   utgangspunkt. Den spør seg frem til et produktkravdokument.
   (`/bmad-product-brief` kan kjøres før, men kravene dekker det meste av
   det en brief skal fange.)

2. **Arkitektur** — `/bmad-architecture`
   Skriver ned de tekniske beslutningene som skal holde delene konsistente.
   Stacken står under «Rammer» i kravene.

3. **Epics og historier** — `/bmad-create-epics-and-stories`
   Bryter PRD og arkitektur ned i historier med akseptansekriterier.

4. **Sprintplanlegging** — `/bmad-sprint-planning`
   Sjekker at planleggingen holder (PASS/CONCERNS/FAIL) og lager
   `sprint-status.yaml`, som byggingen følger.

5. **Bygging** — `/bmad-build`
   Én historie om gangen: avklar, planlegg, implementer, review, presenter.
   Kjør den igjen (i ny kontekst) for neste historie.

Valgfritt etterpå: `/bmad-code-review` for en ekstra review,
`/bmad-qa-generate-e2e-tests` for tester mot API-et.

### Kortere vei

Vil dere heller hoppe over PRD og epics, kondenserer `/bmad-spec
../../oppgave/krav.md` kravene til en kort `SPEC.md` i
`_bmad-output/specs/`. Gi stien til den til `/bmad-build`, så bygger den
rett fra spesifikasjonen. Det er mindre seremoni, men også mindre av det
BMAD er kjent for.

### Greit å vite

- `/bmad-build` sjekker git før den starter, og stopper og spør hvis
  arbeidskatalogen har uncommittede endringer. Andre spor jobber i samme
  repo, så det vil skje — svar at det er greit å fortsette.
- BMAD er satt opp til å snakke og skrive engelsk. Skillene leser
  språket fra to steder, så vil dere ha norsk, må begge endres:
  `communication_language` og `document_output_language` i
  `_bmad/custom/config.toml` (legg til `document_output_language` under
  `[core]`), og de samme to nøklene i `_bmad/core/config.yaml` og
  `_bmad/bmm/config.yaml`.
