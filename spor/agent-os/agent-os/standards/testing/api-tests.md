# Tester

pytest + FastAPIs `TestClient`. Kjøres med `make test` fra `spor/agent-os/`.

- **Hver test får sin egen database.** En fixture peker databasestien mot
  `tmp_path` og overstyrer avhengigheten. Tester deler aldri tilstand.
- Test gjennom HTTP, ikke mot `db.py` direkte. Det er API-et som er produktet.
- **Hvert endepunkt testes både når raden finnes og når den ikke gjør det.**
  404-tilfellet er et krav, ikke en ekstra.
- Egne tester for: flytting mellom lister, at sletting av en liste tar
  gjøremålene med seg, og at data overlever at appen startes på nytt.
- Sjekk statuskode og kropp. `assert r.status_code == 404` alene er for lite.
- Navn sier hva som skjer: `test_henter_gjøremål_i_liste`,
  `test_flytt_til_liste_som_ikke_finnes_gir_404`.
