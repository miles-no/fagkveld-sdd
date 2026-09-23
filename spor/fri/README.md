# fri

Applikasjonen bygges i denne mappen.

Oppdraget står i [`../../oppgave/krav.md`](../../oppgave/krav.md).

Hold deg i denne mappen. De andre sporene løser samme oppgave.

## Før dere starter

For deltakerne, ikke for agenten. Kjøres én gang, fra repo-roten, på
sporets maskin:

```bash
git switch -c spor/fri
cd spor/fri
make install
python3 ../../metrics/tokens.py --start-now
claude
```

- `--start-now` starter klokka for sporet. Kjør den **én gang**, rett før
  dere begynner: kjøres den igjen, flyttes starten, og alt før det nye
  tidspunktet faller ut av målingen.
- `claude` må startes fra denne mappen. Målingen teller etter hvor
  sesjonen ble startet, så en sesjon startet fra repo-roten måles ikke.
- Commit bare denne mappen (`git add spor/fri`), også `metrics/`. Til
  slutt merges branchen inn på `main`.

`make install`, `make run APP=<modul>:<variabel>`, `make test` og
`make lint` kjøres herfra.
