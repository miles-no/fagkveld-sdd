# Tech Stack

Stacken er låst av oppdraget (`../../oppgave/krav.md`, «Rammer»). Ingen nye
avhengigheter skal legges til.

## Frontend

N/A. Produktet er kun et API.

## Backend

- **FastAPI** — ruting, validering og automatisk OpenAPI.
- **Pydantic v2** — modeller for forespørsel og svar.
- **Python 3.12+**, uvicorn som server.

## Database

- **`sqlite3` fra standardbiblioteket.** Ingen ORM, ingen driverpakke.
- Fil på disk, ikke i minnet — data skal overleve omstart.
- Fremmednøkler håndheves eksplisitt (`PRAGMA foreign_keys = ON`).

## Other

- **pytest** + **httpx** til tester, kjøres med `make test`.
- **ruff** til linting, kjøres med `make lint`, linjelengde 100.
- **uv** til avhengigheter, `make install`.
- Kjøring: `make run APP=<modul>:<variabel>` fra `spor/agent-os/`.
