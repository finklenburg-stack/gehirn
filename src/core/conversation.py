from src.storage import db


def get_history_for_prompt(project_id: str) -> list[dict]:
    """Liefert den bisherigen Gespraechsverlauf eines Projekts als
    role/content-Paare fuer die Anthropic Messages API (FR-014, FR-015).
    """
    messages = db.list_messages(project_id)
    return [{"role": m["role"], "content": m["content"]} for m in messages]
