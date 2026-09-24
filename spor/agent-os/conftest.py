"""Gjør app-pakken importerbar når pytest kjøres fra denne mappen."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
