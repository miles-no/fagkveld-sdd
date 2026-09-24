# Fravær og feil

At noe ikke finnes er et normalt svar, ikke et unntak som velter noe.

```json
404  {"detail": "Liste 3 finnes ikke"}
404  {"detail": "Gjøremål 7 finnes ikke"}
```

- Rutelaget slår opp raden og svarer 404 selv. Ingen `try/except` rundt
  manglende rader, ingen 500 fra en `None` som sniker seg videre.
- Meldingen navngir ressursen og id-en. Aldri bare `"Not found"`.
- `GET /lists/{id}/todos` på en liste som ikke finnes er 404, ikke `[]` —
  en tom liste og en liste som ikke eksisterer er ikke det samme.
- Flytting til en liste som ikke finnes er 404 på målisten, ikke 400.
- `DELETE` på noe som ikke finnes er 404. Ikke stille 204.
- Valideringsfeil (tom tittel, feil type) er FastAPIs egen 422. Ikke rør.
