# Husregler

Samme tekst for alle sporene, så ingen får et forsprang de andre mangler.

Reglene ligger allerede som `CLAUDE.md` i hver sporkatalog — Claude Code
leser den filen automatisk for hver sesjon som startes der. Sporene trenger
altså ikke gjøre noe for å få dem, og de trenger ikke lese noe utenfor sin
egen mappe utover briefen.

Denne filen er kilden, og den finnes for ett formål: når et rammeverk
settes opp, skal **samme tekst** legges inn i rammeverkets egen form.

| Spor | Legges i tillegg inn som |
| --- | --- |
| Agent OS | `.agent-os/standards/` |
| Spec Kit | `constitution` |
| BMAD | technical preferences |
| Fri prompting | ingenting mer — `CLAUDE.md` er nok |

Det gjøres **før** sporet stempler start, så det koster ingen tokens. Det er
også det som jevner ut at Agent OS forventer standarder som en forutsetning,
mens Spec Kit og BMAD lager sine inne i arbeidsflyten.

---

Selve teksten ligger i [`spor/agent-os/CLAUDE.md`](spor/agent-os/CLAUDE.md)
og er identisk i alle fire sporene. Kopier derfra, ikke skriv den om — da
er de ikke like lenger.
