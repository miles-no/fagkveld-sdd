# TODO-API — Shaping Notes

## Scope

Et REST-API over to ressurser, lister og gjøremål, med full CRUD på begge,
uthenting av gjøremålene i én bestemt liste, og flytting av et gjøremål fra
én liste til en annen. Hele oppdraget i `../../../../oppgave/krav.md`, ikke
mer.

## Decisions

- **Hybrid API-form.** Nøsting kun der den uttrykker noe: `/lists/{id}/todos`
  for å liste og opprette. Enkeltgjøremål ligger flatt på `/todos/{id}`, så
  URL-en ikke endrer seg når noe flyttes.
- **Flytting er ingen egen mekanisme.** `PATCH /todos/{id}` med `list_id`.
  Hvilken liste et gjøremål hører hjemme i er et felt som alle andre.
- **Fravær er et normalt svar.** Rutelaget slår opp raden og svarer 404 med
  en melding som navngir ressurs og id. Ingen `try/except` rundt manglende
  rader.
- **`GET /lists/{id}/todos` på en liste som ikke finnes er 404, ikke `[]`.**
  En tom liste og en liste som ikke eksisterer er ikke det samme.
- **Cascade i databasen.** Sletting av en liste tar gjøremålene med seg via
  `ON DELETE CASCADE`, ikke via opprydding i rutelaget.
- **`PATCH` er delvis.** Utelatte felt endres ikke. Eksplisitt `null` avvises
  med 422 — ingen av kolonnene tillater NULL, så det er ikke en gyldig verdi.
- **Varighet.** SQLite-fil på disk, stien overstyrbar med `TODO_DB_PATH` slik
  at hver test får sin egen database.

## Context

- **Visuals:** Ingen. Produktet er et API uten grensesnitt.
- **References:** Ingen. Sporet var tomt; det finnes ingen kode å etterligne.
- **Product alignment:** Følger `agent-os/product/roadmap.md` fase 1. Alt i
  fase 2 (paginering, frister, brukere, søk) er bevisst utelatt.

## Standards Applied

- `api/routes` — fastsetter de ti rutene og at flytting er en PATCH.
- `api/errors` — fastsetter 404 som normaltilfelle og formen på meldingen.
- `database/sqlite` — fremmednøkler, cascade, fil på disk, parameterisert SQL.
- `global/structure` — lagdelingen `api → db → models`, og at SQL bare bor i
  `db.py`.
- `testing/api-tests` — isolert database per test, og at hvert endepunkt
  testes både når raden finnes og når den ikke gjør det.
