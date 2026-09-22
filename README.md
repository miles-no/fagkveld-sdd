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

## Ett spor, én branch — og én katalog

Hvert spor jobber på sin egen branch ut fra `main`, med branchnavn på
formen `spor/<navn>` (f.eks. `spor/kiro`). Sporene rører ikke `main`
underveis. Det er disse branchene `metrics/compare.py` plukker opp når
tokenbruken skal stilles side om side til slutt.

Hvert spor trenger også sin egen katalog, ikke bare sin egen branch:

```bash
git worktree add -b spor/<navn> ../spor-<navn> main
cd ../spor-<navn>
```

`metrics/tokens.py` skiller sporene fra hverandre på katalogsti. To spor
som kjører i samme katalog får tokenbruken blandet sammen, og tallene ser
riktige ut selv om de ikke er det.

Hvert spor merker seg selv i `metrics/track.json`, etter mønsteret i
[`metrics/track.example.json`](metrics/track.example.json):

```json
{
  "name": "kiro",
  "framework": "Kiro"
}
```

`framework` settes til `null` for spor som jobber uten rammeverk. Det er
dette feltet sammenligningen bruker til å skille de to gruppene fra
hverandre. `assistant` er valgfri og er `claude-code` som standard.

**Uten `track.json` måler `tokens.py` ingenting.** Det er med vilje: da
skriver den heller ikke målefiler i katalogen du står i, og `main` holder
seg ren. Tidsserien bygges opp fra transkripsjonene hver gang, så du mister
ingen historikk på å opprette filen litt ut i løpet.

## Måleverktøyet

`metrics/` inneholder verktøyet som måler tokenbruken:

| Fil | Innhold |
| --- | --- |
| `metrics/tokens.py` | Leser Claude Code-transkripsjoner og skriver `timeline.json` + `summary.md` |
| `metrics/compare.py` | Leser `timeline.json` fra hver spor-branch og skriver `comparison.md`/`.html` |
| `metrics/track.json` | Sporets navn, rammeverk og assistent |

`tokens.py`, `compare.py` og `track.example.json` er verktøy som ligger på
`main` og arves av alle spor. `track.json`, `timeline.json` og `summary.md`
er **data per spor**: de oppstår i sporets egen katalog og committes på
sporets egen branch. Det er slik `compare.py` finner dem igjen — den leser
`git show <branch>:metrics/timeline.json` for hver spor-branch.

Kun den samlede `comparison.md`/`.html` er gitignorert, siden den genereres
på nytt ved behov.

`.claude/settings.json` har en Stop-hook som kjører
`metrics/tokens.py --quiet`, slik at målingen oppdaterer seg selv.
Presentasjonen ligger i `docs/`.
