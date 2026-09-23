# Fagkveld: spec-driven development

Fire spor bygger samme applikasjon fra samme brief: ett med fri prompting,
tre med hvert sitt SDD-rammeverk. Tokenbruken måles per spor, og etterpå
sammenligner vi forbruk og resultat.

Repoet har med vilje ingen applikasjonskode — den er det sporene lager.

Briefen: [`oppgave/krav.md`](oppgave/krav.md). Utover den får sporene
ingen felles regler.

## Sporene

| Mappe | Rammeverk | Branch |
| --- | --- | --- |
| `spor/agent-os/` | Agent OS | `spor/agent-os` |
| `spor/spec-kit/` | Spec Kit | `spor/spec-kit` |
| `spor/bmad/` | BMAD | `spor/bmad` |
| `spor/fri/` | ingen | `spor/fri` |

Hvert spor har egen maskin og egen branch, og oppstarten står i sporets
`README.md`. Branchene merges inn på `main` når alle sporene er ferdige.

`claude` startes fra sporets mappe. Målingen teller sesjoner etter hvor de
ble startet, så en sesjon startet fra repo-roten måles ikke, og to spor
startet fra samme mappe havner i samme måling.

## Make

```bash
make install                        # uv sync
make run APP=<modul>:<variabel>     # uvicorn --reload
make test                           # pytest; ingen tester er ikke en feil
make lint                           # ruff
```

Kjøres fra repo-roten eller et spor. Avhengighetene er låst i
`pyproject.toml` og `uv.lock` i roten, og alle sporene deler dem.

## Måling

| Fil | Innhold |
| --- | --- |
| `metrics/tokens.py` | leser transkripsjonene, skriver sporets `timeline.json` og `summary.md` |
| `metrics/compare.py` | leser alle `spor/*/metrics/timeline.json`, skriver `comparison.md`/`.html` |
| `spor/<navn>/metrics/track.json` | sporets navn, rammeverk og start |

Stop-hooken i `spor/<navn>/.claude/settings.json` kjører `tokens.py` etter
hvert svar. Uten `track.json` måler `tokens.py` ingenting.

```json
{ "name": "agent-os", "framework": "Agent OS", "assistant": "claude-code" }
```

`framework: null` betyr uten rammeverk, og grafen tegner det stiplet.
`--start-now` legger til `start`, og alt før det tidspunktet utelates. Den
overskriver `start` hver gang, så den kjøres én gang per spor.

Når alle sporene er merget:

```bash
git switch main && git pull
python3 metrics/compare.py                 # tabell og graf
python3 metrics/compare.py --split <ISO>   # før/etter et klokkeslett
```

Spor som ikke er merget, mangler i tabellen.

## Å lese tallene

Agent OS og BMAD front-laster arbeid — standarder, produktdokumenter,
arkitektur — som skal betale seg over mange oppgaver. Én greenfield-kveld
måler investeringen, ikke avkastningen.

## Fasilitator

- `fasilitator/torrkjoring.md`: prøvekjøring av målingen før kvelden.
- `docs/`: presentasjonen.
