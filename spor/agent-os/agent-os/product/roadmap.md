# Product Roadmap

## Phase 1: MVP

Alt kravene ber om:

- **Lister:** opprett, hent alle, hent én, endre navn, slett.
- **Gjøremål:** opprett i en liste, hent én, endre tittel og status, slett.
- **Gjøremål per liste:** hent alle gjøremål som ligger i en bestemt liste.
- **Flytt:** endre hvilken liste et gjøremål hører hjemme i.
- **Fravær som normaltilfelle:** 404 med forklarende kropp når en id ikke
  finnes, både for listen og gjøremålet, og når en flytting peker på en
  liste som ikke finnes.
- **Varighet:** SQLite-fil på disk, skjema opprettes ved oppstart.
- **Tester:** dekker både det som finnes og det som ikke finnes.

## Phase 2: Post-Launch

Utenfor oppdraget, notert så det ikke smyger seg inn i MVP-en:

- Paginering og sortering av gjøremål.
- Frist, prioritet, merkelapper.
- Brukere og tilgangsstyring.
- Søk på tvers av lister.
