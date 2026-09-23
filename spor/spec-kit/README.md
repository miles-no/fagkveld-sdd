# spec-kit

Applikasjonen bygges i denne mappen.

Oppdraget står i [`../../oppgave/krav.md`](../../oppgave/krav.md).

Hold deg i denne mappen. De andre sporene løser samme oppgave.

## Før dere starter

For deltakerne, ikke for agenten. Kjøres én gang, fra repo-roten, på
sporets maskin:

```bash
git switch -c spor/spec-kit
cd spor/spec-kit
make install
python3 ../../metrics/tokens.py --start-now
claude
```

- `--start-now` starter klokka for sporet. Kjør den **én gang**, rett før
  dere begynner: kjøres den igjen, flyttes starten, og alt før det nye
  tidspunktet faller ut av målingen.
- `claude` må startes fra denne mappen. Målingen teller etter hvor
  sesjonen ble startet, så en sesjon startet fra repo-roten måles ikke.
- Commit bare denne mappen (`git add spor/spec-kit`), også `metrics/`. Til
  slutt merges branchen inn på `main`.

`make install`, `make run APP=<modul>:<variabel>`, `make test` og
`make lint` kjøres herfra.

## Oppstart med Spec Kit

Spec Kit er installert i `.specify/` (maler, skript, konstitusjon) og
`.claude/skills/speckit-*` (kommandoene). Kommandoene kjøres som
slash-kommandoer i Claude Code.

Spec Kit har en fast rekkefølge: **konstitusjon → spesifikasjon → plan →
oppgaver → implementering**. Hvert steg skriver en fil som neste steg
leser.

### 1. Konstitusjonen

`.specify/memory/constitution.md` er bare en mal med plassholdere. Den
skal fylles ut først — det er prosjektets prinsipper, og alle senere steg
sjekker seg mot den:

```
/speckit-constitution Utled prinsippene fra ../../oppgave/krav.md.
```

Rammene i kravene (låst stack, ingen nye avhengigheter, data som overlever
omstart) hører naturlig hjemme her. Hvilke prinsipper ellers — for
eksempel om testing og enkelhet — bestemmer dere.

### 2. Spesifikasjonen — *hva* og *hvorfor*

```
/speckit-specify <beskrivelse av oppdraget, eller: se ../../oppgave/krav.md>
```

Skriver `specs/001-<navn>/spec.md` med brukerhistorier og krav, uten
tekniske valg. Uklare punkter merkes `[NEEDS CLARIFICATION]`.

Valgfritt, men anbefalt før planen:

```
/speckit-clarify
```

Stiller opptil fem målrettede spørsmål og skriver svarene inn i
spesifikasjonen.

### 3. Planen — *hvordan*

```
/speckit-plan
```

Her kommer stacken inn. Skriver `plan.md` og tilhørende designfiler
(datamodell, API-kontrakter) i samme `specs/`-mappe, og sjekker planen mot
konstitusjonen.

### 4. Oppgavene

```
/speckit-tasks
```

Bryter planen ned i en ordnet `tasks.md`. Valgfritt etterpå:

```
/speckit-analyze
```

Sjekker at spesifikasjon, plan og oppgaver henger sammen, uten å endre
noe.

### 5. Implementering

```
/speckit-implement
```

Går gjennom `tasks.md` og bygger. Mangler noe etterpå, finner
`/speckit-converge` det som ikke er bygget og legger det til som nye
oppgaver.

`/speckit-checklist` (sjekklister for et område) og
`/speckit-taskstoissues` (GitHub-issues) finnes også, men trengs ikke i
kveld.
