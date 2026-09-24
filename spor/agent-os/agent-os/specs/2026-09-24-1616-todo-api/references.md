# References for TODO-API

## Similar Implementations

Ingen.

Sporet `spor/agent-os/` var tomt da dette arbeidet startet — det fantes ingen
kode å lese mønstre ut av, og ingen tidligere implementasjon å etterligne.
Standardene i `agent-os/standards/` ble derfor utledet fra kravene i stedet
for oppdaget i koden, slik README-en beskriver.

## Kilder som faktisk styrte arbeidet

### Oppdraget

- **Location:** `../../../../oppgave/krav.md`
- **Relevance:** Eneste kilde til hva API-et skal kunne, og til rammene
  (FastAPI, Pydantic, `sqlite3` fra standardbiblioteket, ingen nye
  avhengigheter, data som overlever omstart).

### Produktdokumentasjonen

- **Location:** `../../product/`
- **Relevance:** `roadmap.md` avgrenser hva som hører til MVP-en, og holder
  frister, brukere og paginering utenfor.

### Standardene

- **Location:** `../../standards/`
- **Relevance:** Gjengitt i sin helhet i `standards.md` ved siden av denne
  filen.

## De andre sporene

`spor/bmad/`, `spor/spec-kit/` og `spor/fri/` løser samme oppgave med andre
rammeverk. De er **ikke** referanser — tokenbruken måles per spor, og sporene
skal ikke lese hverandre.
