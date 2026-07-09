"""Setzt vor jedem Import von src.* isolierte Daten-/DB-Pfade, damit Tests
nie die echten Entwicklungsdaten unter data/ beruehren. Muss als Modul-Code
(nicht in einer Fixture) laufen, da pytest conftest.py vor allen Testmodulen
importiert - so sind die Umgebungsvariablen bereits gesetzt, bevor
src.config seine modulweiten Pfad-Konstanten berechnet.
"""

import os
import tempfile
from pathlib import Path

_tmp_dir = Path(tempfile.mkdtemp(prefix="gehirn-test-"))
os.environ.setdefault("APP_DATA_ROOT", str(_tmp_dir / "data"))
os.environ.setdefault("APP_DB_PATH", str(_tmp_dir / "data" / "test.db"))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client():
    from src.main import app

    with TestClient(app) as test_client:
        yield test_client
