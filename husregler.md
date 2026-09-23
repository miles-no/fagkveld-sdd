# Husregler

Gjelder alle spor, og er identiske for alle. De settes opp **før** sporet
stempler start, så de koster ingen tokens.

Hvert rammeverk har sin egen plass for slikt:

| Spor | Legges inn som |
| --- | --- |
| Agent OS | `.agent-os/standards/` |
| Spec Kit | `constitution` |
| BMAD | technical preferences |
| Fri prompting | `CLAUDE.md` i sporets mappe |

## Stacken

Låst i `pyproject.toml` og `uv.lock` i repo-roten: Python 3.12, FastAPI,
Pydantic v2, og `sqlite3` fra standardbiblioteket. Ingen nye avhengigheter.

## Hva vi ønsker

- **Enkelhet framfor fleksibilitet.** Løs oppgaven som står i briefen, ikke
  den du tror kommer etterpå.
- **Skriv for den neste som leser.** Koden blir lest av noen som ikke var
  med da den ble skrevet.
- **Vær konsekvent med deg selv.** Har du først valgt en måte å gjøre noe
  på, gjør det likt neste gang.
- **Gjør det tydelig hva som skjer når noe går galt.** Et kall som ikke kan
  besvares skal svare på en måte den som kalte kan forstå.

## Hva vi med vilje ikke sier noe om

Hvordan koden organiseres — mapper, lag, filnavn, navngiving, hvor grensene
går — bestemmer sporet selv.

Det er ikke en forglemmelse, og det finnes ingen fasit å lete etter i
repoet. Det er nettopp de valgene vi skal se på sammen etterpå.
