# Ruter

Lister og gjøremål er egne ressurser. Nøsting brukes kun der den uttrykker
noe: gjøremål hentes og opprettes under sin liste.

```
POST   /lists                     201  → Liste
GET    /lists                     200  → Liste[]
GET    /lists/{list_id}           200  → Liste
PATCH  /lists/{list_id}           200  → Liste
DELETE /lists/{list_id}           204  → tom kropp

GET    /lists/{list_id}/todos     200  → Gjøremål[]
POST   /lists/{list_id}/todos     201  → Gjøremål

GET    /todos/{todo_id}           200  → Gjøremål
PATCH  /todos/{todo_id}           200  → Gjøremål
DELETE /todos/{todo_id}           204  → tom kropp
```

- Bare disse ti rutene. Ingen `/todos` uten id — gjøremål listes per liste.
- **Flytting er ingen egen rute.** `PATCH /todos/{id}` med `{"list_id": 3}`.
- Id-er i sti, aldri i kropp. `POST /lists/{id}/todos` tar ikke `list_id`.
- Svar er objektet selv, uten konvolutt: `{"id": 1, "name": "Jobb"}`.
- `PATCH` er delvis: felt som utelates, endres ikke. Ikke `PUT`.
