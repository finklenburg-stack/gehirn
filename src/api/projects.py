from fastapi import APIRouter

from src.api.errors import APIError
from src.storage import db
from src.storage import files as file_storage

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", status_code=201)
def create_project(payload: dict):
    name = (payload or {}).get("name")
    if not name or not str(name).strip():
        raise APIError(400, "name_required", "Bitte einen Projektnamen angeben.")
    try:
        return db.create_project(name)
    except db.DuplicateNameError:
        raise APIError(409, "name_taken", "Ein Projekt mit diesem Namen existiert bereits.")


@router.get("")
def list_projects():
    return db.list_projects()


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str):
    project = db.get_project(project_id)
    if project is None:
        raise APIError(404, "not_found", "Projekt existiert nicht.")
    db.delete_project(project_id)
    file_storage.delete_project_dir(project_id)
