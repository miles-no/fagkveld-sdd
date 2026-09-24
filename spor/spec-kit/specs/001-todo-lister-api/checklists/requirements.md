# Specification Quality Checklist: TODO-API med lister

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-24
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`

### Valideringsnotater (runde 1 — alle punkter bestått)

- **Ingen tekniske valg i spec**: Stacken er låst i grunnloven (FastAPI,
  Pydantic, `sqlite3`), men er bevisst holdt utenfor `spec.md`. Det samme gjelder
  HTTP-statuskoder: FR-012 og FR-014 beskriver *at* «finnes ikke» og «ugyldig
  inndata» må være entydig atskilt, ikke at det skjer med 404 og 422. Den
  avbildningen hører hjemme i `plan.md`.
- **Dekning mot kravene**: Alle setninger i `../../oppgave/krav.md` er sporet til
  krav — CRUD for begge entiteter (FR-001–FR-009), gjøremål i en liste (FR-010),
  flytting (FR-011), fravær som normalsituasjon (FR-012–FR-016), varighet
  (FR-017).
- **Ett omstridt valg, dokumentert framfor spurt**: Sletting av en liste sletter
  gjøremålene i den (FR-005). Alternativet — å nekte sletting av en ikke-tom
  liste — er en regel kravene ikke ber om. Valget står i Assumptions med
  begrunnelse og kan overprøves med `/speckit-clarify`.
- **Tom liste vs. liste som ikke finnes** er eksplisitt skilt i Edge Cases, fordi
  det er det lettest oversette tilfellet i FR-012.
