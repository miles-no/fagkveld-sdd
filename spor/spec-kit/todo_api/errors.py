"""Én feilkonvolutt for hele API-et.

FastAPI gir ut av boksen to ulike former: HTTPException gir
{"detail": "<streng>"} og valideringsfeil gir {"detail": [<objekter>]}.
Samme nøkkel, forskjellig type. Håndtererne her normaliserer alt til én form.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class NotFoundError(Exception):
    """Noe det ble vist til finnes ikke. En normal situasjon, ikke et uhell."""

    def __init__(self, resource: str, identifier: int) -> None:
        self.resource = resource
        self.identifier = identifier
        noun = "Liste" if resource == "list" else "Gjøremål"
        super().__init__(f"{noun} {identifier} finnes ikke")


def envelope(
    code: str,
    message: str,
    *,
    resource: str | None = None,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "resource": resource,
            "message": message,
            "details": details or [],
        }
    }


def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=envelope("not_found", str(exc), resource=exc.resource),
    )


def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "loc": [str(part) for part in error.get("loc", [])],
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=envelope("invalid_request", "Ugyldig inndata", details=details),
    )


def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "invalid_request"
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(code, str(exc.detail)),
        headers=getattr(exc, "headers", None),
    )


def register_handlers(app: FastAPI) -> None:
    """Koble håndtererne på applikasjonen.

    _http_handler registreres på Starlettes HTTPException, ikke på FastAPIs.
    Oppslaget av håndterere går gjennom MRO-en til unntaket som faktisk kastes,
    og FastAPIs klasse er en subklasse av Starlettes. Registrert på subklassen
    ville ukjent rute (404) og feil metode (405) sluppet forbi til Starlettes
    standardsvar, med en annen kroppsform enn resten av API-et.
    """
    app.add_exception_handler(NotFoundError, _not_found_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(StarletteHTTPException, _http_handler)
