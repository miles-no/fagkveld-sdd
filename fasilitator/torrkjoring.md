# Tørrkjøring av ett spor

Hensikten er ikke å teste koden — repoet er tomt med vilje. Hensikten er å
bevise at **målekjeden** henger sammen ende til ende:

```
egen sporkatalog → agentarbeid → hooken fyrer → timeline.json →
commit → compare.py → tabell + graf
```

Hvert ledd har en **forventet observasjon**. Ser du noe annet, stopp der —
ikke gå videre.

**Kjør tørrkjøringen i en kastbar katalog, ikke i et av de fire ekte
sporene.** `tokens.py` filtrerer på katalogsti, og transkripsjonene blir
liggende på maskinen etterpå. Tørrkjører du i `spor/bmad`, teller
øvelseskjøringen med i BMADs tall på kvelden.

---

## 0 · Utgangspunkt

```bash
cd <repo-rot>
git status --short
python3 -V
```

**Forventet:** `git status` er tom. `python3` kan være hva som helst fra
3.9 og opp — måleskriptene er gjort bakoverkompatible, så macOS' egen
python (3.9.6) holder.

## 1 · Lag en kastbar sporkatalog

```bash
mkdir -p spor/torrkjoring/metrics spor/torrkjoring/.claude
cp spor/fri/Makefile spor/torrkjoring/
cp spor/fri/.claude/settings.json spor/torrkjoring/.claude/

cat > spor/torrkjoring/metrics/track.json <<'JSON'
{
  "name": "torrkjoring",
  "framework": null,
  "assistant": "claude-code"
}
JSON
```

`track.json` er det som gjør mappen til et spor. Uten den skriver
`tokens.py` ingenting i det hele tatt.

**Forventet:** `cat spor/torrkjoring/.claude/settings.json` viser en
Stop-hook som kaller `../../metrics/tokens.py`. Den relative stien er
riktig — verktøyet ligger bare ett sted, i repo-roten, og deles av sporene.

## 2 · Installer

```bash
make install
```

Kjøres fra **repo-roten**, én gang for alle sporene. `uv` finner
`pyproject.toml` fra undermapper, så sporene deler `.venv` og får identiske
versjoner.

Sjekk at det virker fra sporet også:

```bash
cd spor/torrkjoring
make lint          # All checks passed
make test          # no tests ran — exit 0
```

`make test` skal gi **exit 0** selv om det ikke finnes tester. Målet
tolererer pytests exit 5 med vilje: et rødt byggemål ville fortalt sporet
at noe mangler.

## 3 · Røykteste `tokens.py` FØR agenten jobber

```bash
cd spor/torrkjoring
python3 ../../metrics/tokens.py
```

**Forventet, ordrett:**

```
No messages with a cwd under .../spor/torrkjoring.
```

**Det er riktig svar her.** Steget skiller «scriptet er ødelagt» fra «det
finnes ikke data ennå». Får du i stedet beskjed om at `track.json` mangler,
gikk steg 1 galt.

## 3b · Sett opp rammeverket, og stemple så starten

Dette steget er rekkefølgen som avgjør om oppsettet havner i tallene.

```bash
# 1. installer rammeverket — i sporets mappe, ikke globalt
#    (kjøres i terminalen, koster ingen tokens)

# 2. sjekk at rammeverket ikke tok Stop-hooken med seg
grep tokens.py .claude/settings.json

# 3. start klokka for dette sporet
python3 ../../metrics/tokens.py --start-now
```

**Forventet:** siste kommando svarer `<spor>: teller fra <tidspunkt>` og
legger et `start`-felt i `metrics/track.json`. Alt som er registrert før
det tidspunktet holdes utenfor målingen, også oppsett du gjorde med
assistenten.

Finner ikke steg 2 noe, har rammeverket overskrevet hooken. Legg den inn
igjen før du går videre — ellers måles ikke sporet i det hele tatt.

## 4 · Kjør et kort agentoppdrag

```bash
cd spor/torrkjoring
date -u +%Y-%m-%dT%H:%M:%SZ      # NOTER dette
claude
```

**Kodeassistenten må startes fra sporets egen katalog.** Starter du den fra
repo-roten og jobber på sporet derfra, får meldingene `cwd` = repo-roten,
og `tokens.py` i sporet finner dem ikke. Arbeidet blir umålt.

Gi et lite, avgrenset oppdrag — f.eks. «lag et endepunkt som svarer med
klokkeslettet» — og avslutt sesjonen normalt, ikke med Esc eller ved å
lukke vinduet.

## 5 · Bevis at Stop-hooken fyrte

Hooken er skrevet `2>/dev/null; exit 0` og **feiler helt stille**. Eneste
pålitelige sjekk er tidsstempler mot tidspunktet du noterte i steg 4:

```bash
stat -f '%Sm %N' metrics/timeline.json metrics/summary.md
head -4 metrics/summary.md
python3 -c "import json; d=json.load(open('metrics/timeline.json')); \
print(d['track'], d['framework'], d['assistant'], d['repo_root'], len(d['events']))"
```

**Forventet:** begge filene finnes i `spor/torrkjoring/metrics/`, `mtime`
og `Generated:`-linjen ligger **etter** tidspunktet fra steg 4, `track` er
`torrkjoring`, og `repo_root` slutter på `/spor/torrkjoring`.

| Det du ser | Hva det betyr |
| --- | --- |
| Filene finnes ikke | hooken fyrte ikke — kjør `python3 ../../metrics/tokens.py` manuelt og les beskjeden |
| `repo_root` er repo-roten | du startet assistenten fra roten, ikke fra sporet |
| Færre hendelser enn svar du fikk | forventet hvis du stemplet start i steg 3b — utskriften sier hvor mange eldre som ble utelatt |
| `Every message predates the start time` | du stemplet start etter at arbeidet var gjort; fjern `start` fra `track.json` og kjør på nytt |

## 6 · Commit målingen

```bash
cd <repo-rot>
git add spor/torrkjoring
git status --short
```

**Bare sporets egen mappe.** Alle sporene jobber i samme arbeidstre, så
`git add -A` tar med det de andre driver med. Det er den fellen som vil
bite på kvelden.

Målefilene er vanlige sporede filer — ingen `-f` er nødvendig.

## 7 · Kjør sammenligningen

```bash
cd <repo-rot>
python3 metrics/compare.py
cat metrics/comparison.md
open metrics/comparison.html
```

Ingen `git fetch`, ingen push: `compare.py` leser
`spor/*/metrics/timeline.json` rett fra disk.

**Forventet:** en tabell med `Spor | Rammeverk | Svar | Tokens | Cache |
Tid`, der `torrkjoring` står med `ingen (fri prompting)`. De tre andre
sporene hoppes over med

```
hopper over agent-os: ingen metrics/timeline.json (sporet har ikke blitt målt ennå)
```

som er riktig før kvelden. HTML-en åpner uten nett; spor med rammeverk
tegnes heltrukket, spor uten stiplet.

`--split <ISO-tid>` deler i tillegg tallene i før og etter et klokkeslett.
Du trenger den ikke.

---

## Feller som faktisk vil bite

**Assistenten må startes fra sporets katalog.** Hele isolasjonen hviler på
dette. `tokens.py` tar bare med meldinger med `cwd` under mappen den kjører
i. Startes to spor fra samme mappe, summeres tokenbruken deres under ett
navn, og tallene ser fullstendig plausible ut. Startes et spor fra
repo-roten, blir arbeidet umålt.

**Sporene ser hverandre.** Alle jobber i samme arbeidstre. En agent i
`spor/bmad` kan lese `spor/spec-kit/`, og agenter utforsker. Kommer et spor
sent i gang, kan det finne en ferdig løsning å lene seg på. Vil du unngå
det, må sporene kjøre samtidig — ellers er det en kjent egenskap ved
oppsettet, ikke en overraskelse.

**`git add -A` tar med andres arbeid.** Hvert spor committer kun
`git add spor/<navn>`.

**PATH avgjør om hooken virker.** Hooken arver PATH fra skallet assistenten
ble startet i, og bruker `python3` — ikke uv-miljøet. Skriptene tåler nå
3.9, så systemets python holder, men `python3` må finnes i PATH.

**Rammeverkene kan overskrive `.claude/settings.json`.** Agent OS, BMAD og
Spec Kit legger alle egne hooks der under init. Sjekk at Stop-hooken
fortsatt står **etter** at rammeverket er satt opp:

```bash
grep tokens.py spor/<navn>/.claude/settings.json
```

Finner du ingenting, måles ikke det sporet i det hele tatt.

**Installer rammeverkene på prosjektnivå, ikke på brukernivå.** Legges de i
hjemmekatalogen, havner konfigurasjon og standarder utenfor git og utenfor
tokenmålingen — og et spor kan arve tilstand fra en tidligere sesjon uten
at noe i tallene viser det.

**Avbrutte sesjoner.** Hooken fyrer når hovedagenten blir stille. En sesjon
avbrutt med Esc eller lukket vindu kan gå glipp av den. Kjør derfor
`python3 ../../metrics/tokens.py` manuelt fra sporet (uten `--quiet`, så du
ser tallene) før du committer.

**Fish-syntaks.** `VAR=verdi kommando` virker ikke. Bruk
`env SDD_REPO_ROOT=... python3 ../../metrics/tokens.py`, og `$status` i
stedet for `$?`.

---

## Opprydding

Tørrkjøringen må ikke etterlate spor i kveldens tall.

```bash
cd <repo-rot>

# 1) Fjern den kastbare sporkatalogen
git rm -r --cached spor/torrkjoring 2>/dev/null
rm -rf spor/torrkjoring

# 2) Fjern aggregatet
rm -f metrics/comparison.md metrics/comparison.html

# 3) Fjern transkripsjonene, ellers kan de telles med hvis et ekte spor
#    senere kjøres fra samme katalognavn
ls ~/.claude/projects | grep torrkjoring
rm -rf ~/.claude/projects/<navnet som dukket opp>

# 4) Sluttsjekk
git status --short          # ingen rester fra torrkjoring
python3 metrics/compare.py  # skal si at ingen spor har brukbare data
```

Committet du tørrkjøringen i steg 6, ligger den i historikken. Det gjør
ingen skade så lenge katalogen er slettet — `compare.py` leser disk, ikke
historikk.
