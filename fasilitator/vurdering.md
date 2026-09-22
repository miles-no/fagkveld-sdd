# Vurdering av sporene

Fasilitatornotat. Ligger åpent i repoet.

At sporene kan lese den på forhånd er et bevisst valg: da vet alle hva som
blir sett etter, og siste halvtime blir en felles gjennomgang i stedet for
en dom. Prisen er at sporene kan optimalisere mot de sju punktene, så
resultatene ligner mer på hverandre enn de ellers ville gjort.

Sjekklisten under er skrevet **før** noen kodebase er sett. Det er hele poenget:
sporene bygger samme API fra bunnen av ut fra samme grove brief
(`oppgave/krav.md`), og uten en målestokk som fantes før koden, kollapser
sammenligningen til smak mot smak.

## Slik leser du listen

- Hvert punkt krysses av **Ja / Delvis / Nei** per spor.
- Kryss av på det du faktisk observerer i koden eller i et kjørende API —
  ikke på hva du tror sporet mente.
- Briefen sier med vilje ingenting om organisering. Et spor skal aldri trekkes
  for å ha valgt en annen struktur enn du selv ville valgt. Det trekkes bare
  for å ha valgt **dårlig**, eller for ikke å ha valgt i det hele tatt.
- Bruk maks ~5 minutter per spor per gjennomgang. Rekker du ikke å se det,
  er det i praksis ikke observerbart — sett Delvis og gå videre.

---

## Sjekklisten (7 punkter)

### 1. Svarer API-et fornuftig på noe som ikke finnes?

Hent et gjøremål og en liste med en ID som garantert ikke finnes. Hent
gjøremålene i en ikke-eksisterende liste. Slett noe to ganger. Flytt et
gjøremål til en liste som ikke finnes.

**Ja:** alle gir en veldefinert feilrespons (typisk 404) med en kropp som
sier hva som ikke ble funnet. Ingen stacktrace, ingen 500, ingen tom 200
som later som alt gikk bra.
**Delvis:** noen av veiene er dekket, andre gir 500 eller stilltiende suksess.
**Nei:** serveren kaster, eller svarer 200 på noe som ikke finnes.

### 2. Er ugyldig input avvist før den når databasen?

Send et gjøremål uten tittel, med tom tittel, med feil type på status-feltet,
og med `created`/id satt av klienten. Opprett et gjøremål i en liste som ikke
finnes.

**Ja:** avvises med 4xx og en melding som peker på feltet; ingenting blir
skrevet til databasen.
**Nei:** raden havner i basen, eller feilen kommer som 500 fra sqlite.

### 3. Tåler datamodellen endring?

Still spørsmålet konkret: *hva må jeg endre for å gi et gjøremål en frist
(`due_date`)?* Følg feltet gjennom koden og tell stedene.

**Ja:** feltet har ett tydelig hjem (schema/modell), og endringen treffer et
lite, forutsigbart antall steder. Det finnes en synlig plan for skjemaet —
migrering, versjonering, eller i det minste `CREATE TABLE` samlet ett sted
i stedet for spredt utover.
**Delvis:** feltet må legges til flere steder, men de er lette å finne.
**Nei:** kolonnenavn og feltnavn er duplisert på kryss og tvers, SQL er
strengbygd i endepunktene, og du må lese hele kodebasen for å være sikker
på at du har funnet alle stedene.

### 4. Kan en ny ressurs legges til uten å endre eksisterende filer?

Tenk deg at en `tag` skal inn ved siden av `todo` og `liste`.

**Ja:** det finnes et mønster å kopiere — ny ressurs betyr i hovedsak nye
filer/moduler pluss én registrering. Strukturen er ikke nødvendigvis
lagdelt, men den er *konsekvent*.
**Delvis:** mønsteret finnes, men du må også rote i flere eksisterende filer.
**Nei:** all kode ligger i én fil uten indre struktur, eller strukturen er
inkonsekvent — to ressurser er allerede løst på to ulike måter.

### 5. Er datatilgang skilt fra HTTP?

Let etter `sqlite3`, SQL-strenger og `conn`/`cursor`. Hvor ligger de?

**Ja:** SQL og tilkoblingshåndtering finnes ett sted (modul, klasse,
funksjoner — formen er fri), og endepunktene kaller det. Tilkoblingen
åpnes/lukkes tydelig, ikke som en tilfeldig global.
**Delvis:** stort sett skilt, men enkelte endepunkter snakker direkte med basen.
**Nei:** SQL er inline i hver rute-funksjon.

Merk: data skal overleve omstart (se punkt 7 for hvordan du sjekker det).

### 6. Forklarer koden seg selv for en som ikke skrev den?

Docstring-kravet ble nettopp fjernet fra linteren nettopp for at dette skal
være et observerbart valg, ikke noe verktøyet fremtvinger. Åpne to-tre
tilfeldige filer.

**Ja:** navn er forståelige uten forklaring, og der hvor et valg ikke er
åpenbart (hvorfor denne feilkoden, hvorfor denne tabellstrukturen) står det
en setning om det. En README eller tilsvarende sier hvordan API-et er formet
— hvilke endepunkter finnes, hvordan flytter man et gjøremål. `/docs` fra
FastAPI teller med, hvis endepunktene faktisk har beskrivelser og
responsmodeller.
**Delvis:** enten gode navn uten noen forklaring av valgene, eller
kommentarer som bare gjentar koden.
**Nei:** kryptiske navn, ingen beskrivelse noe sted, `/docs` er tom for
innhold utover metode og sti.

### 7. Finnes det tester, og sier de noe?

Kjør `make test`. Les så testfilene raskt.

**Ja:** testene kjører grønt, og minst én av dem dekker et ikke-funnet-tilfelle
og minst én dekker at data overlever (ny tilkobling / restart / ny klient mot
samme fil). De tester oppførsel gjennom API-et, ikke bare at en funksjon
returnerer det den returnerer.
**Delvis:** tester finnes og kjører, men dekker bare lykkelig sti.
**Nei:** ingen tester, eller de feiler.

---

## Oppsummeringsark

| Punkt | Agent OS | Spec Kit | BMAD | Fri prompting |
|---|---|---|---|---|
| 1. Ikke-funnet | | | | |
| 2. Ugyldig input | | | | |
| 3. Endringsdyktig modell | | | | |
| 4. Ny ressurs | | | | |
| 5. Data vs. HTTP | | | | |
| 6. Forklarer seg selv | | | | |
| 7. Tester | | | | |

---

## Å starte de ukjente kodebasene raskt

Makefile-en i rot-repoet er felles for alle sporene. Den har fire mål:
`install`, `run`, `test`, `lint`. Det viktige er at applikasjonsstien er en
variabel **uten standardverdi**:

    make run APP=<modul>:<variabel>

`make run` uten `APP` stopper med en beskjed om å sette den. Det er med
vilje: repoet tar ikke stilling til hva applikasjonen skal hete eller hvor
den skal ligge, og en standardverdi ville vært et skjult strukturkrav.
Du må altså finne inngangspunktet per spor — se `grep`-trikset under.

Per spor:

    cd spor/<navn>                    # agent-os, spec-kit, bmad, fri
    make test
    make lint
    make run APP=<modul>:<variabel>

(`make install` kjøres én gang fra repo-roten — sporene deler .venv.)

Finner du ikke inngangspunktet, ikke let manuelt:

    grep -rn "FastAPI(" --include=*.py .

Sti-en til `make run` er `<modulsti>:<variabelnavn>` for den filen — f.eks.
`app/main.py` med `app = FastAPI()` blir `APP=app.main:app`.

Når serveren kjører: `http://127.0.0.1:8000/docs` gir deg hele API-flaten
uten å lese en linje kode. Det er raskeste vei inn i punkt 1, 2 og 6.

Sjekk av punkt 5/7 (data overlever omstart): opprett en liste og et gjøremål,
stopp serveren med Ctrl-C, start den igjen, hent det samme. Merk at
`--reload` skjuler dette — en reload er ikke en restart av prosessens
databasefil hvis noen har lagt data i minnet; stopp helt.

Databasefiler er gitignorert (`*.db`), så hvert spor lager sin egen i sin
egen katalog. Finner du ingen, har sporet enten valgt et annet filnavn
eller ikke fått persistens til å virke — punkt 5 og 7 skiller de to.

---

## Les tokentallene sammen med sjekklisten

`metrics/tokens.py` bygger tidsserien per spor fra Claude Code-transkriptene,
og `metrics/compare.py` samler alle sporene til én tabell og et SVG-diagram
som kan projiseres. Kjøres fra repo-roten, leser `spor/*/metrics/`:

    python3 metrics/compare.py

Tabellen har en egen rammeverk-kolonne, og en gruppetabell som summerer
med mot uten rammeverk. Merkingen kommer fra `spor/<navn>/metrics/track.json`
— står det feil rammeverk der, står det feil i tabellen.

### To forbehold som må sies høyt før tallene vises

**Engangskostnad mot løpende kostnad.** Agent OS og BMAD front-laster arbeid
som er ment å betale seg over mange oppgaver — standarder, produktdokumenter,
arkitekturbeslutninger. En enkelt greenfield-kveld måler investeringen, ikke
avkastningen. Blir konklusjonen «seremoni er dyrt», er det delvis et artefakt
av formatet og ikke bare en egenskap ved rammeverkene. Si det før søylene
vises, ikke etterpå.

**Installer Agent OS på prosjektnivå.** Standardene skal ligge i `.agent-os/`
i sporets egen mappe (`spor/agent-os/.agent-os/`), ikke i `~/.agent-os/`.
Da blir de sporet av git, committet sammen med resten av sporet, og tokenene
for å skrive dem havner i målingen — alt er etterprøvbart etterpå.

Ligger de på brukernivå i stedet, er de usynlige for både git og
`tokens.py`: skrevet i en tidligere sesjon teller de ikke, og sporet starter
med et forsprang ingen av de andre har. Sjekk `ls ~/.agent-os` før kvelden;
finnes den, noter hva som ligger der.

Ingen av tallene er en konklusjon alene. Sjekklisten sier *hvor bra*,
metrikken sier *hvor dyrt*. Funnet ligger i kombinasjonen:

- **Høy kvalitet, lav tokenkostnad** — rammeverket betalte seg.
- **Høy kvalitet, høy tokenkostnad** — et helt annet funn. Kvaliteten kom,
  men den ble kjøpt. Spørsmålet blir om prisen er verdt det, ikke om
  metoden virker.
- **Lav kvalitet, høy tokenkostnad** — det dyreste utfallet, og det mest
  lærerike.
- **Lav kvalitet, lav tokenkostnad** — kan være et helt rimelig valg for
  små oppgaver. Ikke automatisk en fiasko.

Si dette høyt før tallene vises på skjerm. Ellers leser rommet den laveste
søylen som vinneren.
