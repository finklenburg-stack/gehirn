import shutil
import uuid
from pathlib import Path

from src.config import DATA_ROOT


def project_documents_dir(project_id: str) -> Path:
    path = DATA_ROOT / project_id / "documents"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_pdf(project_id: str, filename: str, content: bytes) -> str:
    """Speichert die PDF-Datei unter einem eindeutigen Namen und gibt den Pfad zurueck."""
    target_dir = project_documents_dir(project_id)
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    target_path = target_dir / unique_name
    target_path.write_bytes(content)
    return str(target_path)


def delete_document_file(storage_path: str) -> None:
    path = Path(storage_path)
    if path.exists():
        path.unlink()


def delete_project_dir(project_id: str) -> None:
    project_dir = DATA_ROOT / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)
