# Fagkveld: spec-driven development

Dette er rot-prosjektet for en fagkveld om spec-driven development (SDD).
Flere spor bygger den samme applikasjonen fra bunnen av, ut fra den samme
grove briefen. Ett spor jobber med fri prompting, de andre bruker hvert
sitt SDD-rammeverk. Underveis måles tokenbruken per spor, slik at sporene
kan sammenlignes mot hverandre etterpå — både på forbruk og på hva de
endte opp med.

Repoet inneholder med vilje ingen applikasjonskode. Det er sporet som
skriver den, og hvordan den blir seende ut er nettopp det eksperimentet
skal vise.

## Oppdraget

Briefen sporene jobber etter ligger i [`oppgave/krav.md`](oppgave/krav.md).

Utover briefen får sporene ingen felles regler. `CLAUDE.md` i hver
sporkatalog sier bare hvor briefen ligger, at organiseringen er sporets
eget valg, og at sesjonen hører hjemme i den mappen.

## Kom i gang

```bash
make install
```

### Makefile-mål

| Mål | Kjører |
| --- | --- |
| `make install` | `uv sync` |
| `make run` | `uv run uvicorn $(APP) --reload` |
| `make test` | `uv run pytest` |
| `make lint` | `uv run ruff check .` |

`make run` krever at `APP` settes på kommandolinjen — det finnes ingen
standardverdi, fordi repoet ikke tar stilling til hva applikasjonen skal
hete eller hvor den skal ligge: `make run APP=<modul>:<variabel>`.

## Stack

Avhengighetene er låst i `pyproject.toml` og `uv.lock`:

- Python 3.12 (`requires-python = ">=3.12"`), pinnet i `.python-version`
- [uv](https://docs.astral.sh/uv/) for avhengigheter og kjøring
- FastAPI (>=0.115) og Uvicorn (>=0.32, `standard`-ekstra)
- Pydantic v2 (>=2.9)
- SQLite gjennom `sqlite3` i standardbiblioteket — ingen ORM
- Utviklingsgruppe: pytest (>=8.3), httpx (>=0.27), ruff (>=0.7)

Ruff er satt opp med linjelengde 100 og regelsettene `E`, `F`, `I`,
`UP` og `B`.

## Ett spor, én mappe

Hvert spor har sin egen mappe under `spor/`, og jobber bare der:

```
spor/agent-os/     Agent OS
spor/spec-kit/     Spec Kit
spor/bmad/         BMAD
spor/fri/          fri prompting
```

**Start kodeassistenten fra sporets egen mappe**, ikke fra repo-roten:

```bash
cd spor/agent-os
claude
```

Det er ikke en formalitet. `metrics/tokens.py` skiller sporene fra
hverandre på katalogsti. Startes to spor fra samme mappe, havner
tokenbruken deres i samme måling, og tallene ser riktige ut selv om de
ikke er det.

Målingen teller sesjoner etter **hvor de ble startet**. Alt en sesjon som
ble startet i sporet gjør, telles for sporet — også om den beveger seg
underveis. Og en sesjon som ble startet et annet sted telles aldri for
sporet, selv om den skulle innom.

Konsekvensen er at en sesjon startet fra repo-roten ikke måles i det hele
tatt, uansett hvor mye den jobber på sporet. Derfor `cd` inn i mappen
først.

Hver sporkatalog har sin egen `.claude/settings.json` med Stop-hooken, sin
egen `Makefile`, og sin egen `metrics/`. Avhengighetene er låst i
`pyproject.toml` og `uv.lock` i repo-roten, og `uv` finner dem fra en
undermappe — så `make install` fra sporet gir samme versjoner uten at
sporet trenger et eget prosjekt.

### Merking

`spor/<navn>/metrics/track.json` sier hvem sporet er:

```json
{
  "name": "agent-os",
  "framework": "Agent OS",
  "assistant": "claude-code"
}
```

`framework` settes til `null` for spor som jobber uten rammeverk. Det er
dette feltet sammenligningen bruker til å skille de to gruppene fra
hverandre. `assistant` er valgfri og er `claude-code` som standard.

`start` er valgfri og settes når sporet faktisk begynner. Alt som er
registrert før det tidspunktet holdes utenfor målingen:

```bash
cd spor/agent-os
python3 ../../metrics/tokens.py --start-now
```

Kjør den **én gang per spor**, på sporets maskin. Den overskriver `start`
hver gang, så kjøres den igjen midt i sporet, faller alt før det nye
tidspunktet ut av målingen uten at noe sier fra.

Det er slik oppsettet av rammeverket holdes utenfor tallene. Selve
installasjonen koster uansett ingenting — `tokens.py` teller bare meldinger
fra kodeassistenten, ikke kommandoer du kjører i terminalen. Men har du
brukt assistenten i sporkatalogen på forhånd, ligger de meldingene i
transkripsjonene og telles med til du stempler starten.

`tokens.py` finner sporet ved å lete oppover etter `metrics/track.json` fra
der den kjøres. Den virker altså også om assistenten står i en undermappe
av sporet, og finner ingenting om den kjøres utenfor et spor.

**Uten `track.json` måler `tokens.py` ingenting.** Det er med vilje: da
skriver den heller ikke målefiler i mappen du står i, så repo-roten holder
seg ren. Tidsserien bygges opp fra transkripsjonene hver gang, så du
mister ingen historikk på å opprette filen litt ut i løpet.

## Måleverktøyet

| Fil | Innhold |
| --- | --- |
| `metrics/tokens.py` | Leser transkripsjoner og skriver sporets `timeline.json` + `summary.md` |
| `metrics/compare.py` | Leser alle sporenes `timeline.json` og skriver `comparison.md`/`.html` |
| `spor/<navn>/metrics/track.json` | Sporets navn, rammeverk og assistent |

Verktøyet ligger ett sted, i `metrics/` i repo-roten, og deles av alle
sporene — Stop-hooken i hvert spor kaller `../../metrics/tokens.py`.
Måledataene er derimot per spor og havner i `spor/<navn>/metrics/`.

Til slutt, fra repo-roten:

```bash
python3 metrics/compare.py
```

Den leser `spor/*/metrics/timeline.json`, skriver en tabell med en kolonne
for rammeverk, og en graf der spor uten rammeverk tegnes stiplet.
`--split <ISO-tid>` deler i tillegg tallene i før og etter et klokkeslett.

Sporenes `timeline.json`, `summary.md` og `track.json` committes som
vanlige filer. Kun den samlede `comparison.md`/`.html` er gitignorert,
siden den genereres på nytt ved behov.

Målingen oppdaterer seg selv: `spor/<navn>/.claude/settings.json` har en
Stop-hook som kjører etter hvert svar fra agenten.

### Å lese tallene

Kvaliteten på det sporene lager går vi gjennom sammen. Tallene er bare den
ene halvdelen, og to ting er verdt å si høyt før de vises:

**Engangskostnad mot løpende kostnad.** Rammeverk som Agent OS og BMAD
front-laster arbeid — standarder, produktdokumenter, arkitekturbeslutninger
— som er ment å betale seg over mange oppgaver. Én greenfield-kveld måler
investeringen, ikke avkastningen. Blir konklusjonen «seremoni er dyrt», er
det delvis et artefakt av formatet.

**Rammeverkene må installeres i sporets egen mappe**, ikke i hjemmekatalogen.
Legges de globalt, havner konfigurasjon og standarder utenfor både git og
tokenmålingen, og et spor kan arve tilstand fra en tidligere sesjon uten at
noe i tallene viser det.

## Fasilitatornotater

`fasilitator/torrkjoring.md` beskriver hvordan måleoppsettet prøvekjøres på
et kastbart spor før kvelden. Den ligger åpent — ingenting i dette repoet er
skjult for sporene.

Presentasjonen ligger i `docs/`.
