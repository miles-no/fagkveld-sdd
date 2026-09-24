<!--
Sync Impact Report (midlertidig — fjernes før commit av amendert grunnlov)
- Versjon: TEMPLATE (ufylt) → 1.0.0
- Bump-begrunnelse: Første ratifisering. Alle plassholdere erstattet med
  konkrete prinsipper utledet fra ../../oppgave/krav.md.
- Endrede prinsipper:
  - [PRINCIPLE_1_NAME] → I. Kravene avgrenser omfanget
  - [PRINCIPLE_2_NAME] → II. Låst stack
  - [PRINCIPLE_3_NAME] → III. Varig lagring
  - [PRINCIPLE_4_NAME] → IV. Fravær er et normalt svar
  - [PRINCIPLE_5_NAME] → V. Oppførsel verifiseres med tester
- Lagt til seksjoner:
  - Tekniske rammer (fra [SECTION_2_NAME])
  - Arbeidsflyt og kvalitetsporter (fra [SECTION_3_NAME])
- Fjernede seksjoner: ingen
- Utsatte TODO-er: ingen
-->

# TODO-API Constitution

## Core Principles

### I. Kravene avgrenser omfanget

`../../oppgave/krav.md` er eneste kilde til hva som skal bygges. Funksjonalitet som
ikke følger av kravene MÅ utelates: ingen autentisering, ingen brukere, ingen
paginering, ingen frister, ingen prioriteringer, ingen tagger, ingen mykt slett,
ingen bakgrunnsjobber — med mindre kravene senere endres og grunnloven amenderes.
Modeller, endepunkter og lag som ikke tjener et formulert krav er brudd.

Begrunnelse: Oppdraget er lite og presist. Hvert tillegg utover kravene er kode
ingen har bedt om, som likevel må vedlikeholdes, testes og forsvares.

### II. Låst stack

Kun FastAPI, Pydantic og `sqlite3` fra standardbiblioteket. Ingen nye
kjøretidsavhengigheter MÅ legges til — ikke SQLAlchemy, ikke en ORM, ikke en
migreringsmotor, ikke en driver. `pyproject.toml` i repo-roten er uendret av dette
sporet. Testverktøyet som allerede finnes (`pytest`, `httpx`, `ruff`) er tillatt.

Begrunnelse: Rammen er eksplisitt i kravene. Den tvinger fram at datalaget skrives
for hånd, som er hele poenget med oppgaven.

### III. Varig lagring

All tilstand MÅ ligge i en SQLite-fil på disk. Data skrevet gjennom API-et MÅ være
tilgjengelig etter omstart av prosessen. Ingen modulglobal dict, ingen liste i
minnet, ingen `:memory:`-database som produksjonslager. Skjemaet MÅ opprettes
idempotent ved oppstart, slik at en tom fil og en eksisterende fil begge virker.
Relasjonen gjøremål→liste MÅ håndheves i databasen med fremmednøkkel.

Begrunnelse: «Data skal overleve en omstart» er et uttrykt krav, og
fremmednøkkelen er det som hindrer at et gjøremål ender opp i en liste som ikke
finnes.

### IV. Fravær er et normalt svar

Oppslag mot noe som ikke finnes MÅ besvares med en veldefinert HTTP-respons — ikke
et unntak som slipper ut, ikke en 500, ikke en tom 200 som skjuler feilen.
Konkret: ukjent liste eller gjøremål gir 404 med en forklarende meldingskropp;
ugyldig inndata gir 422; sletting av noe som ikke finnes gir 404. Feilsvar MÅ ha
samme kroppsform gjennom hele API-et.

Begrunnelse: Kravene sier rett ut at dette er en normal situasjon. Et API som
krasjer på et slikt oppslag har feilet på selve oppdraget.

### V. Oppførsel verifiseres med tester

Hvert krav i spesifikasjonen MÅ ha minst én automatisert test som kjører mot
API-et via FastAPIs `TestClient`. Testsuiten MÅ dekke både den lykkelige stien og
fraværstilfellene fra prinsipp IV, inkludert flytting av et gjøremål til en liste
som ikke finnes. Tester MÅ kjøre mot en isolert, midlertidig databasefil og ikke
avhenge av hverandres rekkefølge eller etterlatte data.

Begrunnelse: Kravene er formulert som oppførsel. Tester er den eneste måten å vise
at oppførselen faktisk stemmer, og isolasjon er det som gjør dem til bevis
framfor tilfeldigheter.

## Tekniske rammer

- Python ≥ 3.12, slik repo-roten allerede krever.
- Kjøres med `make run APP=<modul>:<variabel>` fra `spor/spec-kit`.
- All SQL skrives for hånd mot `sqlite3` med parameteriserte spørringer.
  Strenginterpolering av verdier inn i SQL er forbudt.
- Fremmednøkler MÅ slås på eksplisitt per tilkobling (`PRAGMA foreign_keys = ON`),
  siden `sqlite3` har dem av som standard.
- Pydantic-modeller utgjør API-ets kontrakt. Rader fra databasen MÅ konverteres til
  modeller før de forlater datalaget; `sqlite3.Row` lekker ikke ut i rutene.
- Koden MÅ ligge under `spor/spec-kit`. Ingen filer utenfor denne mappen endres,
  med unntak av `metrics/` som verktøyet selv skriver.

## Arbeidsflyt og kvalitetsporter

- Rekkefølgen er Spec Kit sin: constitution → specify → plan → tasks → implement.
  Et steg leser det forrige steget skrev.
- Tekniske valg hører hjemme i `plan.md`, ikke i `spec.md`.
- `make test` og `make lint` MÅ begge være grønne før en oppgave regnes som
  ferdig. Ruff er konfigurert i repo-roten med `E`, `F`, `I`, `UP`, `B` og
  linjelengde 100.
- Når en oppgave viser seg å kreve noe grunnloven forbyr, endres grunnloven først
  — koden får ikke gå rundt den stilltiende.

## Governance

Denne grunnloven går foran andre vaner og preferanser i dette sporet. Ved
motstrid mellom grunnloven og et senere Spec Kit-artefakt vinner grunnloven, og
artefaktet MÅ rettes.

Amendering krever at endringen skrives inn i denne filen, at versjonen økes etter
semantisk versjonering, og at `Last Amended` settes til endringsdatoen:

- MAJOR: et prinsipp fjernes eller redefineres på en måte som ugyldiggjør
  eksisterende artefakter.
- MINOR: et nytt prinsipp eller en ny seksjon legges til, eller veiledning utvides
  vesentlig.
- PATCH: presiseringer, ordlyd og rettinger uten endret betydning.

Etterlevelse sjekkes ved hvert Spec Kit-steg: `/speckit-plan` og
`/speckit-tasks` MÅ kontrollere planen og oppgavene mot prinsippene, og
`/speckit-analyze` MÅ rapportere avvik. Kompleksitet utover det kravene tilsier MÅ
begrunnes skriftlig i `plan.md` eller fjernes. `CLAUDE.md` i sporets rot gir
kjøretidsveiledning og MÅ ikke motsi denne grunnloven.

**Version**: 1.0.0 | **Ratified**: 2026-09-24 | **Last Amended**: 2026-09-24
