"""Avhengigheter som deles av ruterne.

Aliaset ligger her og ikke i ``db.py``, fordi ``Depends`` er HTTP og
datalaget ikke skal kjenne til HTTP.
"""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import Depends

from app.db import get_connection

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]
