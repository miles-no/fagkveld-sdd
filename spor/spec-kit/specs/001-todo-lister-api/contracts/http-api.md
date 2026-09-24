# Contract: HTTP-API

**Spec**: [../spec.md](../spec.md) | **Modeller**: [../data-model.md](../data-model.md)

Alle kropper er JSON. Alle id-er er heltall; en id på feil form gir 422 uten at
endepunktet kjøres (D-003).

## Feilkonvolutt

Hvert feilsvar — uansett endepunkt og uansett statuskode — har denne formen
(FR-016):

```json
{
  "error": {
    "code": "not_found",
    "resource": "list",
    "message": "Liste 42 finnes ikke",
    "details": []
  }
}
```

| Felt | Betydning |
| --- | --- |
| `code` | `"not_found"` eller `"invalid_request"` |
| `resource` | `"list"` eller `"todo"` ved `not_found`, ellers `null` |
| `message` | Menneskelesbar forklaring. Klienter skal ikke tolke den |
| `details` | Feltvise valideringsfeil ved `invalid_request`, ellers `[]` |

`resource` er det som lar en klient skille «ukjent liste» fra «ukjent gjøremål» i
ett og samme kall (FR-013, SC-007).

### Statuskoder

| Kode | Når |
| --- | --- |
| 200 | Vellykket henting eller endring |
| 201 | Vellykket oppretting |
| 204 | Vellykket sletting, ingen kropp |
| 404 | Liste eller gjøremål finnes ikke (FR-012) |
| 404 | Ukjent sti — rammeverkets eget svar, men i samme konvolutt |
| 405 | Feil HTTP-metode mot en kjent sti — også i samme konvolutt |
| 422 | Ugyldig inndata: tom tittel/navn, ukjent felt, id på feil form (FR-014) |

Ingen annen kode forekommer ved normal bruk. 500 er per FR-015 en feil i seg
selv.

FR-016 gjelder **alle** feilsvar, også de rammeverket genererer på egen hånd før
et endepunkt er nådd. De to siste radene er derfor ikke en detalj: håndteres de
ikke, har API-et to ulike kroppsformer, og en klient som tolker feil likt overalt
brekker på den ene av dem.

---

## Lister

### `POST /lists` → 201

Oppretter en liste. **FR-001**

```json
→ {"name": "Handel"}
← {"id": 1, "name": "Handel"}
```

Feil: 422 ved tomt eller kun-blankt navn, manglende `name`, eller ukjent felt.

### `GET /lists` → 200

Alle lister, sortert på `id` stigende. **FR-002**

```json
← [{"id": 1, "name": "Handel"}, {"id": 2, "name": "Jobb"}]
```

Tom samling når ingen lister finnes — ikke en feil.

### `GET /lists/{list_id}` → 200

Én liste. **FR-003**

Feil: 404 `resource: "list"`.

### `PATCH /lists/{list_id}` → 200

Endrer navnet. Gjøremålene i listen røres ikke. **FR-004**

```json
→ {"name": "Matbutikk"}
← {"id": 1, "name": "Matbutikk"}
```

Tom kropp `{}` er lovlig og gir listen uendret tilbake (D-008).
Feil: 404 `resource: "list"`, 422 ved tomt navn.

### `DELETE /lists/{list_id}` → 204

Sletter listen **og gjøremålene i den** (FR-005, INV-2). Andre listers gjøremål
berøres ikke.

Feil: 404 `resource: "list"` — også ved andre sletting av samme liste.

---

## Gjøremål

### `POST /lists/{list_id}/todos` → 201

Oppretter et gjøremål i listen. **FR-006**

```json
→ {"title": "Kjøpe melk"}
← {"id": 1, "title": "Kjøpe melk", "done": false, "list_id": 1}
```

`done` kan oppgis ved oppretting; utelatt betyr `false`.
Feil: 404 `resource: "list"` når listen ikke finnes (FR-012, ikke en 500 fra
fremmednøkkelen — D-005). 422 ved tom tittel.

### `GET /lists/{list_id}/todos` → 200

Gjøremålene i én liste, sortert på `id` stigende. **FR-010**

```json
← [{"id": 1, "title": "Kjøpe melk", "done": false, "list_id": 1}]
```

En liste uten gjøremål gir `[]`. En liste som **ikke finnes** gir 404 — de to er
forskjellige situasjoner, og dette er kravets lettest oversette kanttilfelle.

### `GET /todos/{todo_id}` → 200

Ett gjøremål, med hvilken liste det hører til. **FR-007**

Feil: 404 `resource: "todo"`.

### `PATCH /todos/{todo_id}` → 200

Endrer `title`, `done`, eller begge. Felt som ikke sendes forblir uendret
(FR-008, D-008). Endrer aldri `list_id` — det gjør bare `/move`.

```json
→ {"done": true}
← {"id": 1, "title": "Kjøpe melk", "done": true, "list_id": 1}
```

Tom kropp `{}` gir gjøremålet uendret tilbake.
Feil: 404 `resource: "todo"`, 422 ved tom tittel eller ukjent felt (`list_id`
avvises her).

### `DELETE /todos/{todo_id}` → 204

Sletter gjøremålet. Listen det lå i berøres ikke. **FR-009**

Feil: 404 `resource: "todo"`.

### `POST /todos/{todo_id}/move` → 200

Flytter gjøremålet til en annen liste. `id`, `title` og `done` er uendret.
**FR-011**

```json
→ {"list_id": 2}
← {"id": 1, "title": "Kjøpe melk", "done": false, "list_id": 2}
```

Flytting til listen gjøremålet allerede ligger i lykkes og er uten effekt.

Feil: 404 med `resource: "todo"` hvis gjøremålet ikke finnes, 404 med
`resource: "list"` hvis mållisten ikke finnes. Ved det siste blir gjøremålet
liggende urørt der det er (FR-019). Dette kallet er grunnen til at `resource`
finnes i konvolutten.

---

## Sporing mot kravene

| Krav | Dekkes av |
| --- | --- |
| FR-001 | `POST /lists` |
| FR-002 | `GET /lists` |
| FR-003 | `GET /lists/{id}` |
| FR-004 | `PATCH /lists/{id}` |
| FR-005 | `DELETE /lists/{id}` |
| FR-006 | `POST /lists/{id}/todos` |
| FR-007 | `GET /todos/{id}` |
| FR-008 | `PATCH /todos/{id}` |
| FR-009 | `DELETE /todos/{id}` |
| FR-010 | `GET /lists/{id}/todos` |
| FR-011 | `POST /todos/{id}/move` |
| FR-012, FR-013 | 404 + `resource` på alle endepunkter over |
| FR-014 | 422 + `details` |
| FR-015 | Ingen 500 i noen rad over |
| FR-016 | Feilkonvolutten, brukt av alle tre håndtererne |

Elleve endepunkter dekker de ti operasjonene i SC-001 (`GET /lists` og
`GET /lists/{id}` er begge «hente lister»).
