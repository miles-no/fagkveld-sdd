# agent-os

Applikasjonen bygges i denne mappen.

Oppdraget står i [`../../oppgave/krav.md`](../../oppgave/krav.md).

Hold deg i denne mappen. De andre sporene løser samme oppgave.

Sesjonen må startes her: målingen teller etter hvor sesjonen ble startet,
så en sesjon startet fra repo-roten måles ikke.

`make install`, `make run APP=<modul>:<variabel>`, `make test` og
`make lint` kjøres herfra.

## Oppstart med Agent OS

Agent OS er installert i `.claude/commands/agent-os/` og `agent-os/`.
Kommandoene kjøres som slash-kommandoer i Claude Code: `/plan-product`,
`/discover-standards`, `/index-standards`, `/inject-standards` og
`/shape-spec`.

Agent OS kommer **uten standarder** — `agent-os/standards/index.yml` er
tom. Det er meningen: standardene skal beskrive dette prosjektets måte å
gjøre ting på. Siden prosjektet er greenfield, finnes det ingen kode å
hente dem ut fra, så de må utledes fra kravene.

### 1. Produktdokumentasjon

```
/plan-product
```

Svar ut fra [`../../oppgave/krav.md`](../../oppgave/krav.md). Stacken står
under «Rammer» i kravene. Resultatet havner i `agent-os/product/`
(`mission.md`, `roadmap.md`, `tech-stack.md`).

### 2. Standarder utledet fra kravene

`/discover-standards` er laget for å lese mønstre ut av eksisterende kode.
Her er det ingen, så pek den mot kravene i stedet:

```
/discover-standards Det finnes ingen kode ennå. Utled standardene fra
../../oppgave/krav.md og agent-os/product/tech-stack.md i stedet for fra
kodebasen.
```

Kommandoen går gjennom ett område om gangen, spør om begrunnelsen og ber
om godkjenning før hver fil skrives. Kravene peker selv på noen områder
det er naturlig å ta stilling til:

- hvordan API-et er formet (ressurser, operasjoner, statuskoder)
- hvordan «finnes ikke» og andre feil besvares
- hvordan data lagres i `sqlite3` så de overlever en omstart
- hvordan koden testes

Hva standardene faktisk sier, bestemmer dere. Filene havner i
`agent-os/standards/<område>/`. Har du skrevet eller endret standarder for
hånd, oppdater indeksen med:

```
/index-standards
```

### 3. Forme spesifikasjonen

`/shape-spec` må kjøres i **plan mode** (Shift+Tab til plan mode er på):

```
/shape-spec
```

Den leser produktdokumentene og foreslår relevante standarder fra
indeksen. Oppgave 1 i planen er alltid å lagre spesifikasjonen i
`agent-os/specs/<tidsstempel>-<navn>/`. Godkjenn planen, så går
implementeringen i gang.

### Underveis

`/inject-standards` henter relevante standarder inn i samtalen når du
jobber utenfor en plan, for eksempel ved en rettelse etter første runde.
