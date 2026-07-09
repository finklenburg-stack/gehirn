from fastapi import APIRouter

from src.api.errors import APIError
from src.core.claude_client import AIUnavailableError, ContextTooLargeError, ask_question
from src.storage import db

router = APIRouter(prefix="/api/projects", tags=["chat"])


def _require_project(project_id: str) -> dict:
    project = db.get_project(project_id)
    if project is None:
        raise APIError(404, "not_found", "Projekt existiert nicht.")
    return project


@router.post("/{project_id}/messages", status_code=201)
def post_message(project_id: str, payload: dict):
    project = _require_project(project_id)

    content = (payload or {}).get("content")
    if not content or not str(content).strip():
        raise APIError(400, "content_required", "Bitte eine Frage eingeben.")

    if db.count_ready_documents(project_id) == 0:
        raise APIError(
            409, "no_documents", "Diesem Projekt sind noch keine verarbeiteten Dokumente zugeordnet."
        )

    db.create_message(project_id, "user", content)

    try:
        result = ask_question(project_id, project["name"], content)
    except ContextTooLargeError as exc:
        raise APIError(413, "context_too_large", str(exc))
    except AIUnavailableError as exc:
        raise APIError(502, "ai_unavailable", str(exc))

    return db.create_message(project_id, "assistant", result["content"], result["sources"])


@router.get("/{project_id}/messages")
def get_messages(project_id: str):
    _require_project(project_id)
    return db.list_messages(project_id)
