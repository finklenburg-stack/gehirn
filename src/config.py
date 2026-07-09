import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_ROOT = Path(os.environ.get("APP_DATA_ROOT", "data"))
DB_PATH = Path(os.environ.get("APP_DB_PATH", str(DATA_ROOT / "app.db")))

ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_CONTEXT_CHARS = int(os.environ.get("MAX_CONTEXT_CHARS", "600000"))


class MissingAPIKeyError(Exception):
    """Wird ausgeloest, wenn kein ANTHROPIC_API_KEY konfiguriert ist (Prinzip V)."""


def get_anthropic_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise MissingAPIKeyError(
            "ANTHROPIC_API_KEY ist nicht gesetzt. Bitte in .env oder als "
            "Umgebungsvariable hinterlegen (siehe .env.example)."
        )
    return key
