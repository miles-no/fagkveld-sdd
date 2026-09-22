# Oppdrag

Lag et API for gjøremål (TODO) og lister, fra bunnen av.

## Hva det skal kunne

Et gjøremål har en tittel og en status som sier om det er gjort eller
ikke. En liste har et navn. Hvert gjøremål hører hjemme i én liste.

Gjennom API-et skal man kunne opprette, hente, endre og slette både
gjøremål og lister. Man skal kunne hente gjøremålene som ligger i en
bestemt liste, og man skal kunne flytte et gjøremål fra én liste til en
annen.

Spørringer etter noe som ikke finnes er en normal situasjon, ikke et
uhell. API-et svarer fornuftig på dem i stedet for å bryte sammen.

## Rammer

- Stacken er låst: FastAPI, Pydantic og `sqlite3` fra
  standardbiblioteket. Ingen nye avhengigheter.
- Data skal overleve en omstart av applikasjonen.

Alt annet — hvordan API-et er formet, hvordan koden er organisert, hva
ting heter — avgjør du selv.
