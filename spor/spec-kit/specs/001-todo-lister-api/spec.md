# Feature Specification: TODO-API med lister

**Feature Branch**: `spor/spec-kit`

**Created**: 2026-09-24

**Status**: Draft

**Input**: User description: "Et API for gjøremål (TODO) og lister. Et gjøremål har en tittel og en status som sier om det er gjort eller ikke. En liste har et navn. Hvert gjøremål hører hjemme i én liste. Gjennom API-et skal man kunne opprette, hente, endre og slette både gjøremål og lister. Man skal kunne hente gjøremålene som ligger i en bestemt liste, og man skal kunne flytte et gjøremål fra én liste til en annen. Spørringer etter noe som ikke finnes er en normal situasjon, ikke et uhell — API-et svarer fornuftig på dem i stedet for å bryte sammen."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Samle gjøremål i en liste (Priority: P1)

En klient oppretter en liste med et navn, legger et gjøremål inn i den, og henter
ut gjøremålene som ligger i nettopp den listen. Dette er kjernen: uten dette er
det ingenting å hente, endre eller flytte.

**Why this priority**: Dette er minste fungerende produkt. Er bare denne bygget,
kan en klient likevel bruke API-et til å holde orden på oppgaver.

**Independent Test**: Kan testes alene ved å opprette en liste, opprette ett
gjøremål i den, og hente listens gjøremål — svaret inneholder gjøremålet som ble
opprettet, og ingenting annet.

**Acceptance Scenarios**:

1. **Given** et tomt API, **When** klienten oppretter en liste med navn «Handel»,
   **Then** får den tilbake listen med en id som kan brukes videre.
2. **Given** en liste som finnes, **When** klienten oppretter et gjøremål med
   tittel «Kjøpe melk» i den listen, **Then** opprettes gjøremålet med status
   «ikke gjort», og det peker på den listen.
3. **Given** en liste med to gjøremål og en annen liste med ett, **When**
   klienten henter gjøremålene i den første listen, **Then** returneres nøyaktig
   de to, og ikke gjøremålet fra den andre listen.
4. **Given** en liste uten gjøremål, **When** klienten henter listens gjøremål,
   **Then** returneres en tom samling — ikke en feil.

---

### User Story 2 - Holde gjøremål oppdatert (Priority: P2)

En klient henter et enkelt gjøremål, retter tittelen, markerer det som gjort, og
sletter det når det ikke lenger er relevant.

**Why this priority**: Et gjøremål som aldri kan krysses av eller rettes er lite
verdt. Dette er det som gjør listen levende, men det forutsetter at P1 finnes.

**Independent Test**: Kan testes alene ved å opprette ett gjøremål, endre status
til gjort, hente det igjen og se den nye statusen, og deretter slette det og se
at det er borte.

**Acceptance Scenarios**:

1. **Given** et gjøremål med status «ikke gjort», **When** klienten setter status
   til «gjort», **Then** gjenspeiler et påfølgende oppslag den nye statusen.
2. **Given** et gjøremål, **When** klienten endrer tittelen, **Then** beholdes
   status og listetilhørighet uendret.
3. **Given** et gjøremål, **When** klienten sletter det, **Then** finnes det ikke
   lenger, og listen det lå i finnes fortsatt.
4. **Given** en endring som bare angir status, **When** den sendes inn, **Then**
   endres bare status — tittelen kreves ikke på nytt.

---

### User Story 3 - Flytte et gjøremål mellom lister (Priority: P3)

En klient flytter et gjøremål fra listen det ligger i, til en annen liste.

**Why this priority**: Uttrykt krav, og den eneste operasjonen som berører
forholdet mellom de to entitetene. Den bygger på at begge finnes fra før, og er
derfor sist av kjerneoperasjonene.

**Independent Test**: Kan testes alene ved å opprette to lister og ett gjøremål i
den første, flytte det til den andre, og verifisere at det nå dukker opp i den
andre listens gjøremål og er borte fra den første.

**Acceptance Scenarios**:

1. **Given** et gjøremål i liste A og en liste B som finnes, **When** klienten
   flytter gjøremålet til B, **Then** hører gjøremålet nå hjemme i B, med tittel
   og status uendret.
2. **Given** det samme gjøremålet etter flyttingen, **When** klienten henter
   gjøremålene i A, **Then** er gjøremålet ikke med.
3. **Given** et gjøremål i liste A, **When** klienten «flytter» det til A igjen,
   **Then** lykkes operasjonen og gjøremålet blir liggende i A.

---

### User Story 4 - Forvalte listene (Priority: P4)

En klient får oversikt over alle lister, henter én bestemt liste, gir en liste
nytt navn, og sletter en liste som ikke lenger brukes.

**Why this priority**: Kompletterer kravet om at lister skal kunne opprettes,
hentes, endres og slettes. Nyttig, men ingen er blokkert uten det så lenge
listene kan opprettes i P1.

**Independent Test**: Kan testes alene ved å opprette to lister, hente oversikten
og se begge, gi den ene nytt navn, slette den andre, og hente oversikten igjen.

**Acceptance Scenarios**:

1. **Given** to lister, **When** klienten henter alle lister, **Then** er begge
   med i svaret.
2. **Given** en liste, **When** klienten gir den nytt navn, **Then** gjenspeiler
   et påfølgende oppslag det nye navnet, og listens gjøremål er urørt.
3. **Given** en liste med gjøremål i, **When** klienten sletter listen, **Then**
   slettes listens gjøremål sammen med den, og andre listers gjøremål berøres
   ikke.

---

### Edge Cases

- **Ukjent id ved oppslag**: Klienten spør etter en liste eller et gjøremål som
  ikke finnes. Svaret er et tydelig «finnes ikke»-svar med forklaring, ikke et
  sammenbrudd og ikke et tomt «alt gikk bra».
- **Gjøremål i en liste som ikke finnes**: Klienten forsøker å opprette et
  gjøremål i en ukjent liste, eller å hente gjøremålene i en ukjent liste. Begge
  besvares som «finnes ikke» — ikke som en tom samling, siden en tom liste og en
  liste som ikke eksisterer er forskjellige situasjoner.
- **Flytting til en liste som ikke finnes**: Gjøremålet blir liggende urørt der
  det er, og klienten får «finnes ikke» som svar.
- **Sletting to ganger**: Første sletting lykkes, andre gir «finnes ikke».
  Ingen av delene bryter API-et.
- **Tom eller kun-blanke tittel/navn**: Avvises som ugyldig inndata, tydelig
  atskilt fra «finnes ikke».
- **Id på feil form**: En id som ikke har forventet form behandles som ugyldig
  inndata, ikke som et sammenbrudd.
- **Duplikater**: To lister kan hete det samme, og to gjøremål kan ha samme
  tittel. Dette er tillatt og skal ikke avvises.
- **Omstart**: API-et stanses og startes på nytt. Alt som var lagret, er der
  fortsatt, med samme id-er.

## Requirements *(mandatory)*

### Functional Requirements

**Lister**

- **FR-001**: Systemet MÅ kunne opprette en liste ut fra et navn, og gi den en id
  som er unik og stabil over tid.
- **FR-002**: Systemet MÅ kunne returnere alle lister.
- **FR-003**: Systemet MÅ kunne returnere én bestemt liste ut fra id.
- **FR-004**: Systemet MÅ kunne endre navnet på en eksisterende liste.
- **FR-005**: Systemet MÅ kunne slette en liste ut fra id. Gjøremålene som hører
  til listen slettes sammen med den.

**Gjøremål**

- **FR-006**: Systemet MÅ kunne opprette et gjøremål med en tittel, knyttet til
  nøyaktig én eksisterende liste. Et nytt gjøremål starter med status «ikke
  gjort» med mindre klienten oppgir noe annet.
- **FR-007**: Systemet MÅ kunne returnere ett bestemt gjøremål ut fra id, med
  tittel, status og hvilken liste det hører til.
- **FR-008**: Systemet MÅ kunne endre et gjøremåls tittel og status, hver for seg
  eller samtidig. Felt som ikke oppgis forblir uendret.
- **FR-009**: Systemet MÅ kunne slette et gjøremål ut fra id, uten at listen det
  lå i påvirkes.
- **FR-010**: Systemet MÅ kunne returnere alle gjøremål som hører til en bestemt
  liste.
- **FR-011**: Systemet MÅ kunne flytte et gjøremål til en annen eksisterende
  liste, uten at tittel, status eller id endres.

**Fravær og feil**

- **FR-012**: Enhver operasjon som viser til en liste eller et gjøremål som ikke
  finnes, MÅ besvares med et «finnes ikke»-svar som er entydig skilt fra både
  vellykkede svar og fra svar om ugyldig inndata.
- **FR-013**: «Finnes ikke»-svaret MÅ si hva som ikke ble funnet, slik at en
  klient kan skille en ukjent liste fra et ukjent gjøremål i samme kall.
- **FR-014**: Ugyldig inndata (tom tittel, tomt navn, id på feil form, manglende
  påkrevde felt) MÅ besvares med et eget svar for ugyldig inndata, med angivelse
  av hva som er galt.
- **FR-015**: Ingen operasjon — verken gyldig, ugyldig eller mot noe som ikke
  finnes — MÅ få systemet til å stoppe, henge eller svare med en uhåndtert feil.
- **FR-016**: Alle feilsvar MÅ ha samme form gjennom hele API-et, slik at en
  klient kan tolke dem likt uansett hvilket kall som feilet.

**Varighet og integritet**

- **FR-017**: Alle data MÅ overleve en omstart av applikasjonen, med samme id-er
  og samme innhold som før omstarten.
- **FR-018**: Systemet MÅ garantere at ethvert gjøremål til enhver tid hører
  hjemme i nøyaktig én liste som finnes. Et gjøremål uten liste, eller med
  referanse til en slettet liste, MÅ ikke kunne oppstå.
- **FR-019**: En operasjon som feiler MÅ ikke etterlate delvis lagrede endringer.

### Key Entities

- **Liste**: En navngitt samling av gjøremål. Har en id som identifiserer den
  entydig, og et navn valgt av klienten. Kan inneholde null eller flere gjøremål.
- **Gjøremål**: En enkelt oppgave. Har en id som identifiserer det entydig, en
  tittel, en status som sier om det er gjort eller ikke, og en tilhørighet til
  nøyaktig én liste. Tilhørigheten kan endres; da flytter gjøremålet.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Alle åtte kjerneoperasjonene — opprett, hent, endre og slett, for
  både lister og gjøremål — er tilgjengelige gjennom API-et, samt henting av en
  listes gjøremål og flytting mellom lister. 10 av 10 dekket.
- **SC-002**: En klient kan gå fra ingenting til «første gjøremål registrert» med
  to kall.
- **SC-003**: 100 % av oppslag mot id-er som ikke finnes besvares med et «finnes
  ikke»-svar. Null sammenbrudd og null uhåndterte feil i testsuiten.
- **SC-004**: Etter en full omstart er 100 % av tidligere lagrede lister og
  gjøremål tilgjengelige med uendret innhold og uendrede id-er.
- **SC-005**: Hvert funksjonelle krav (FR-001 til FR-019) er dekket av minst én
  automatisert test, og hele testsuiten er grønn.
- **SC-006**: Det finnes ingen måte å få et gjøremål til å ligge i en liste som
  ikke finnes — verken ved oppretting, flytting eller sletting av liste.
  Verifisert med tester for alle tre veiene.
- **SC-007**: Hvert svar fra API-et er entydig klassifiserbart som lykkes,
  «finnes ikke» eller ugyldig inndata, uten at klienten må granske
  meldingsteksten.

## Assumptions

- **Sletting av en liste sletter gjøremålene i den.** Kravene sier at hvert
  gjøremål hører hjemme i én liste. Et gjøremål uten liste ville derfor vært en
  tilstand spesifikasjonen ikke har noe navn på. Alternativet — å nekte å slette
  en liste som ikke er tom — ble valgt bort fordi det ville innført en regel
  kravene ikke ber om.
- **Ingen brukere, ingen tilgangskontroll.** Kravene nevner ingen aktører utover
  «man». API-et er åpent, og alle klienter ser samme data.
- **Ett enkelt løpende system.** Ingen krav om flere samtidige instanser, replikering
  eller synkronisering mellom noder.
- **Status er binær.** «Gjort eller ikke gjort» leses bokstavelig; ingen
  mellomtilstander som «påbegynt» eller «avlyst».
- **Ingen rekkefølge på gjøremål.** Kravene nevner ikke sortering eller
  prioritering. Gjøremålene i en liste returneres i en forutsigbar rekkefølge,
  men klienten kan ikke bestemme den.
- **Ingen paginering, filtrering eller søk.** Datamengden antas liten nok til at
  hele samlinger kan returneres.
- **Ingen historikk.** Sletting er endelig; det finnes ingen papirkurv og ingen
  logg over endringer.
- **Klienten er et program, ikke et menneske.** Suksesskriteriene måles i kall og
  svar, ikke i skjermbilder eller klikk; det finnes ingen brukergrensesnitt i
  dette omfanget.
