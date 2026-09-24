# Phase 0: Research — TODO-API med lister

**Dato**: 2026-09-24 | **Spec**: [spec.md](./spec.md) | **Grunnlov**: [constitution.md](../../.specify/memory/constitution.md)

Stacken er låst av grunnloven (prinsipp II), så forskningen handler ikke om *hva*
som skal brukes, men om *hvordan* de låste delene settes sammen uten å bryte
prinsipp III (varig lagring), IV (fravær er et normalt svar) og V (testbarhet).

## Verifisert miljø

Målt i repoets `.venv` 2026-09-24, ikke antatt:

| Komponent | Versjon |
| --- | --- |
| Python | 3.12.11 |
| SQLite (biblioteket bak `sqlite3`) | 3.53.4 |
| FastAPI | 0.141.1 |
| Pydantic | 2.13.5 |

SQLite 3.53 er godt over 3.35, som er terskelen for `RETURNING`. Det er relevant
for D-006.

---

## D-001: Fremmednøkler må slås på per tilkobling

**Decision**: Hver nye tilkobling kjører `PRAGMA foreign_keys = ON` før den brukes
til noe annet. Skjemaet erklærer `ON DELETE CASCADE` på `todos.list_id`.

**Rationale**: Målt i dette miljøet:

```text
PRAGMA foreign_keys  →  (0,)     # av som standard
PRAGMA foreign_keys=ON  →  (1,)
INSERT INTO t(title, list_id) VALUES('y', 999)
  →  sqlite3.IntegrityError: FOREIGN KEY constraint failed
DELETE FROM l WHERE id=1  →  1 rad slettet, 0 gjøremål igjen
```

Uten pragmaet er `REFERENCES` i skjemaet ren dokumentasjon: ugyldig `list_id`
slipper gjennom og `ON DELETE CASCADE` gjør ingenting. Det ville brutt FR-018
stille. Pragmaet er per tilkobling, ikke lagret i filen, så det må settes hver
gang — dette er den enkeltfeilen som er lettest å gjøre i denne oppgaven.

**Alternatives considered**: Håndheve relasjonen i Python (sjekke at listen finnes
før innsetting) — forkastet fordi det er en sjekk som kan glemmes på ett kallsted,
mens databasen håndhever den alltid. Vi gjør *begge deler*: eksplisitt sjekk for å
gi et pent 404 (D-005), og fremmednøkkel som nett under.

---

## D-002: Én tilkobling per forespørsel, via FastAPI-avhengighet

**Decision**: En `Depends`-funksjon åpner en `sqlite3.Connection`, setter
`row_factory` og pragmaet, yielder den, og lukker den i `finally`. Stien ligger på
`app.state`.

**Rationale**: FastAPI kjører `def`-endepunkter (ikke `async def`) i en
trådpool, så to forespørsler kan lande på ulike tråder. En delt modulglobal
tilkobling ville krevd `check_same_thread=False` og egen låsing. Å åpne en
SQLite-tilkobling er mikrosekunder — det er en filhåndtak, ikke et nettverkskall
— så per forespørsel er både tryggest og enklest. `finally` garanterer lukking
også når et endepunkt kaster.

**Alternatives considered**: Global tilkobling med `check_same_thread=False` og en
`threading.Lock` — forkastet som unødvendig kompleksitet (prinsipp I).
Tilkoblingspool — forkastet; ville krevd en avhengighet vi ikke har lov til.

---

## D-003: Heltalls-id fra `INTEGER PRIMARY KEY`

**Decision**: `id INTEGER PRIMARY KEY` på begge tabeller. Rutene tar `int` i
stien.

**Rationale**: SQLite gir dette gratis som alias for `rowid`, stabilt over
omstart (FR-017). Bonus for FR-014: når stiparameteren er annotert `int`, avviser
FastAPI `/lists/abc` med 422 av seg selv — «id på feil form» er dekket uten egen
kode, og faller automatisk i riktig kategori (ugyldig inndata, ikke «finnes
ikke»).

Merk at `INTEGER PRIMARY KEY` uten `AUTOINCREMENT` kan gjenbruke en id etter
sletting. Det er akseptabelt her: spesifikasjonen krever unike id-er blant
eksisterende rader, ikke globalt unike for all framtid, og det finnes ingen
historikk (Assumptions).

**Alternatives considered**: UUID-strenger — forkastet; løser et
distribusjonsproblem vi ikke har, og gjør «feil form» vanskeligere å skille fra
«finnes ikke». `AUTOINCREMENT` — forkastet; legger til en `sqlite_sequence`-tabell
for en garanti ingen har bedt om.

---

## D-004: Én feilkonvolutt for hele API-et

**Decision**: Alle feilsvar har samme form:

```json
{ "error": { "code": "not_found", "resource": "list", "message": "...", "details": [] } }
```

Tre unntakshåndterere normaliserer inn i den: domenets `NotFoundError` → 404,
`RequestValidationError` → 422, og `HTTPException` → sin egen statuskode.

**Rationale**: FR-016 krever én form. Ut av boksen gir FastAPI to *ulike* former:
`HTTPException` gir `{"detail": "<streng>"}`, mens valideringsfeil gir
`{"detail": [<liste med objekter>]}`. Samme nøkkel, forskjellig type — en klient
som gjør `data["detail"].upper()` krasjer på annenhver feil. Håndtererne fjerner
den fella.

`resource`-feltet er det som oppfyller FR-013: i `POST /lists/{id}/todos` kan
404-en bety «listen finnes ikke», og i `POST /todos/{id}/move` kan den bety enten
«gjøremålet finnes ikke» eller «mållisten finnes ikke». Klienten skiller dem på
`resource`, ikke på meldingsteksten (SC-007).

**Alternatives considered**: Beholde FastAPIs standardform — forkastet, bryter
FR-016. RFC 9457 `application/problem+json` — forkastet som overdrevet for
omfanget; formen over dekker det samme behovet.

---

## D-005: Eksplisitt eksistenssjekk foran skrivingen

**Decision**: Skriveoperasjoner som viser til en liste (opprett gjøremål, flytt
gjøremål) sjekker først at listen finnes og kaster `NotFoundError` hvis ikke.

Sjekken og skrivingen deler **ikke** transaksjon. Det trengs ikke: hver operasjon
har nøyaktig én skriving, så det finnes ingen delvis tilstand å etterlate
(FR-019). Med `isolation_level=''` kjører en `SELECT` uansett utenfor
transaksjonen — den åpnes først ved `INSERT`/`UPDATE` — så en påstand om felles
transaksjon ville vært feil.

**Rationale**: Uten sjekken ville en ukjent `list_id` gitt
`sqlite3.IntegrityError`, som er en 500 med mindre den fanges. FR-012 krever 404.
Å oversette `IntegrityError` til 404 i stedet er mulig, men unøyaktig: den samme
unntakstypen dekker flere brudd, og vi ville gjettet hvilket. Sjekken gir et
presist `resource`-felt.

Sjekk-så-skriv har et teoretisk kappløp (listen slettes mellom sjekk og
innsetting). Det gjør ingen skade her: fremmednøkkelen fanger det, og resultatet
blir 500 i et vindu på mikrosekunder i en enprosess-applikasjon uten samtidige
skrivere (Assumptions). Vi betaler ikke for mer låsing enn det.

---

## D-006: `RETURNING` framfor `lastrowid` + nytt oppslag

**Decision**: `INSERT ... RETURNING id, ...` og `UPDATE ... RETURNING ...` henter
den lagrede raden i samme setning.

**Rationale**: Verifisert i dette miljøet (`RETURNING: (1, 'A')`). Det sparer et
rundturs-oppslag, og viktigere: det som returneres til klienten er garantert den
raden databasen faktisk har, ikke en Python-modell vi trodde vi skrev.

**Alternatives considered**: `cursor.lastrowid` etterfulgt av `SELECT` —
fungerer, men er to setninger og to steder å ta feil. `lastrowid` brukes uansett
ikke ved `UPDATE`.

---

## D-007: `rowcount` avgjør 204 mot 404 ved sletting

**Decision**: `DELETE` kjøres direkte; `cursor.rowcount == 0` betyr at ingenting
fantes → `NotFoundError`. Ingen `SELECT` først.

**Rationale**: Målt: `DELETE` av en eksisterende rad gir `rowcount == 1`. Én
setning, atomisk, og dekker FR-012 for sletting samt kanttilfellet «sletting to
ganger» uten ekstra spørring.

---

## D-008: Delvis oppdatering med `exclude_unset`

**Decision**: PATCH-modellene har felt med `None` som standard, og ruten bruker
`model_dump(exclude_unset=True)` til å bygge `SET`-delen dynamisk. Tomt objekt
gir uendret rad og 200.

**Rationale**: FR-008 krever at felt som ikke oppgis forblir uendret. Å se på
verdien er ikke nok — Pydantic kan ikke skille «ikke sendt» fra «sendt som null»
på verdien alene, men `model_fields_set` (som `exclude_unset` bygger på) kan.
Uten dette ville `{"done": true}` nullet ut tittelen.

**Alternatives considered**: PUT med full erstatning — forkastet; FR-008 sier
eksplisitt «hver for seg eller samtidig».

---

## D-009: Flytting er et eget endepunkt

**Decision**: `POST /todos/{todo_id}/move` med kroppen `{"list_id": <int>}`.
`PATCH /todos/{todo_id}` endrer *ikke* listetilhørighet.

**Rationale**: FR-011 beskriver flytting som en egen operasjon med egen
feilsituasjon — mållisten kan mangle. Et eget endepunkt gjør den 404-en entydig
plassert, og holder PATCH-en til «tittel og status», som er akkurat det FR-008
sier. Å blande `list_id` inn i PATCH ville gitt ett endepunkt med to ulike
404-betydninger og en uklar kontrakt.

Dette er det ene stedet planen legger til noe utover en rå CRUD-form. Det er
begrunnet i et uttrykt krav, ikke i smak, og bryter derfor ikke prinsipp I.

**Alternatives considered**: `PATCH /todos/{id}` med `list_id` i kroppen —
forkastet som over. `PUT /lists/{id}/todos/{todo_id}` — forkastet; modellerer
flytting som to ressursers problem og gjør stien tvetydig.

---

## D-010: Transaksjoner med `with conn:`

**Decision**: Hver skriveoperasjon pakkes i `with conn:`. Lesing går utenfor.

**Rationale**: `isolation_level` er `''` (målt), altså den eldre implisitte
modusen: `sqlite3` åpner en transaksjon ved første DML og holder den åpen til
commit. `with conn:` committer ved normal utgang og ruller tilbake ved unntak.
Det er akkurat FR-019 — ingen delvis lagrede endringer.

Merk at dette er et sikkerhetsnett, ikke det som bærer FR-019 i dag: ingen av
operasjonene skriver mer enn én rad, så det finnes ingenting å rulle delvis
tilbake (se D-005). `with conn:` er der for at det skal fortsette å stemme hvis
en operasjon senere får to skrivinger.

**Alternatives considered**: `conn.autocommit` (nytt i 3.12) — forkastet; ny og
mindre kjent semantikk uten gevinst her. Manuelle `BEGIN`/`COMMIT` — forkastet;
`with` gjør tilbakerullingen vanskelig å glemme.

---

## D-011: Databasesti fra miljøvariabel, app-fabrikk for testene

**Decision**: `create_app(db_path=None)` bygger applikasjonen. Stien hentes fra
`TODO_DB_PATH`, med `todo.db` i arbeidskatalogen som standard. Modulnivå:
`app = create_app()`. Skjemaet opprettes idempotent (`CREATE TABLE IF NOT
EXISTS`) ved oppstart.

**Rationale**: Prinsipp V krever at tester kjører mot en isolert, midlertidig
fil. En fabrikk lar hver test bygge en app mot sin egen `tmp_path`, uten
miljøvariabel-triksing og uten at testene ser hverandres data. Idempotent skjema
er prinsipp III: tom fil og eksisterende fil må begge virke, og det er også det
som gjør omstartstesten (FR-017) mulig — to apper mot samme fil etter hverandre.

`app = create_app()` på modulnivå er det `make run APP=todo_api.main:app`
trenger.

**Alternatives considered**: `sqlite3.connect(":memory:")` i tester — forkastet;
ville ikke testet at data faktisk overlever, og per-forespørsel-tilkoblingene fra
D-002 ville fått hver sin tomme database.

---

## D-012: Engelske navn i kode og JSON

**Decision**: Dokumentasjonen er på norsk, koden og JSON-feltene er på engelsk:
`list`, `todo`, `title`, `done`, `name`, `list_id`.

**Rationale**: Norsk i identifikatorer gir blandingsformer som `liste_id` ved
siden av FastAPIs egne engelske navn, og æ/ø/å i JSON-nøkler. Oppdraget selv
kaller det «TODO». Valget er konsistens, ikke preferanse — det viktige er at det
er *ett* valg, brukt overalt.

---

## Åpne punkter

Ingen. Ingen `NEEDS CLARIFICATION` gjensto fra spesifikasjonen, og ingen oppsto
under designet.
