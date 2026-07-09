from fastapi import APIRouter, UploadFile

from src.api.errors import APIError
from src.core.pdf_extraction import PDFExtractionError, extract_pages
from src.storage import db
from src.storage import files as file_storage

router = APIRouter(prefix="/api/projects", tags=["documents"])


def _require_project(project_id: str) -> dict:
    project = db.get_project(project_id)
    if project is None:
        raise APIError(404, "not_found", "Projekt existiert nicht.")
    return project


@router.post("/{project_id}/documents", status_code=202)
async def upload_document(project_id: str, file: UploadFile):
    _require_project(project_id)

    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise APIError(400, "invalid_file_type", "Nur PDF-Dateien werden akzeptiert.")

    content = await file.read()
    storage_path = file_storage.save_pdf(project_id, filename, content)
    document = db.create_document(project_id, filename, storage_path)

    try:
        pages = extract_pages(storage_path)
    except PDFExtractionError as exc:
        db.update_document_status(document["id"], "failed", error_message=str(exc))
        return {"id": document["id"], "filename": filename, "status": "failed", "error_message": str(exc)}

    db.save_document_pages(document["id"], pages)
    db.update_document_status(document["id"], "ready", page_count=len(pages))
    return {"id": document["id"], "filename": filename, "status": "ready", "page_count": len(pages)}


@router.get("/{project_id}/documents")
def list_documents(project_id: str):
    _require_project(project_id)
    return db.list_documents(project_id)


@router.delete("/{project_id}/documents/{document_id}", status_code=204)
def delete_document(project_id: str, document_id: str):
    _require_project(project_id)
    document = db.get_document(document_id)
    if document is None or document["project_id"] != project_id:
        raise APIError(404, "not_found", "Dokument existiert nicht.")
    db.delete_document(document_id)
    file_storage.delete_document_file(document["storage_path"])
