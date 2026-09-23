# agent-os

Oppdraget: [`../../oppgave/krav.md`](../../oppgave/krav.md). Bygg i denne
mappen; de andre sporene løser samme oppgave i sine.

## Før dere starter

For deltakerne, ikke agenten. Fra repo-roten:

```bash
git switch -c spor/agent-os
cd spor/agent-os
make install
python3 ../../metrics/tokens.py --start-now   # én gang; ny kjøring flytter starten
claude                                        # herfra, ellers måles ikke sesjonen
```

Commit bare `spor/agent-os` (inkludert `metrics/`). Branchen merges inn på
`main` til slutt.

`make run APP=<modul>:<variabel>`, `make test` og `make lint` kjøres herfra.

## Agent OS

Kommandoene ligger i `.claude/commands/agent-os/`. Standardene i
`agent-os/standards/` er tomme — prosjektet er greenfield, så de utledes
fra kravene.

1. **Produkt.** Svar ut fra kravene; stacken står under «Rammer».

   ```
   /plan-product
   ```

   Skriver `agent-os/product/mission.md`, `roadmap.md` og `tech-stack.md`.

2. **Standarder.** `/discover-standards` leser vanligvis mønstre ut av
   koden. Det finnes ingen, så pek den mot kravene:

   ```
   /discover-standards Det finnes ingen kode ennå. Utled standardene fra
   ../../oppgave/krav.md og agent-os/product/tech-stack.md.
   ```

   Kravene peker på API-form, svar når noe ikke finnes, lagring som tåler
   omstart, og testing. Hva standardene sier, bestemmer dere. Etter
   håndredigering: `/index-standards`.

3. **Spesifikasjon.** Krever plan mode (Shift+Tab):

   ```
   /shape-spec
   ```

   Første oppgave i planen lagrer spesifikasjonen i
   `agent-os/specs/<tidsstempel>-<navn>/`. Godkjenn planen for å bygge.

`/inject-standards` henter standardene inn i samtalen utenfor en plan.
