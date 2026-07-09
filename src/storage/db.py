import json
import sqlite3
import uuid
from datetime import datetime, timezone

from src.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    page_count INTEGER,
    status TEXT NOT NULL DEFAULT 'processing',
    error_message TEXT,
    uploaded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);

CREATE TABLE IF NOT EXISTS document_pages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    UNIQUE(document_id, page_number)
);
CREATE INDEX IF NOT EXISTS idx_document_pages_document_id ON document_pages(document_id);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    sources TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_project_id ON messages(project_id);
"""


class NotFoundError(Exception):
    pass


class DuplicateNameError(Exception):
    pass


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Projekte -----------------------------------------------------------

def create_project(name: str) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    project_id = str(uuid.uuid4())
    created_at = _now()
    conn = get_connection()
    try:
        try:
            conn.execute(
                "INSERT INTO projects (id, name, created_at) VALUES (?, ?, ?)",
                (project_id, name, created_at),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateNameError("name_taken") from exc
    finally:
        conn.close()
    return {"id": project_id, "name": name, "created_at": created_at}


def list_projects() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.created_at,
                   COUNT(d.id) AS document_count
            FROM projects p
            LEFT JOIN documents d ON d.project_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_project(project_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, created_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_project(project_id: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --- Dokumente ------------------------------------------------------------

def create_document(project_id: str, filename: str, storage_path: str) -> dict:
    document_id = str(uuid.uuid4())
    uploaded_at = _now()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO documents (id, project_id, filename, storage_path, status, uploaded_at)
            VALUES (?, ?, ?, ?, 'processing', ?)
            """,
            (document_id, project_id, filename, storage_path, uploaded_at),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": document_id,
        "project_id": project_id,
        "filename": filename,
        "storage_path": storage_path,
        "status": "processing",
        "page_count": None,
        "error_message": None,
        "uploaded_at": uploaded_at,
    }


def update_document_status(
    document_id: str, status: str, page_count: int | None = None, error_message: str | None = None
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE documents SET status = ?, page_count = ?, error_message = ? WHERE id = ?",
            (status, page_count, error_message, document_id),
        )
        conn.commit()
    finally:
        conn.close()


def save_document_pages(document_id: str, pages: list[str]) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM document_pages WHERE document_id = ?", (document_id,))
        conn.executemany(
            "INSERT INTO document_pages (id, document_id, page_number, text) VALUES (?, ?, ?, ?)",
            [
                (str(uuid.uuid4()), document_id, page_number, text)
                for page_number, text in enumerate(pages, start=1)
            ],
        )
        conn.commit()
    finally:
        conn.close()


def list_documents(project_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, filename, page_count, status, error_message, uploaded_at
            FROM documents
            WHERE project_id = ?
            ORDER BY uploaded_at ASC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_document(document_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, project_id, filename, storage_path, status FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_document(document_id: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def count_ready_documents(project_id: str) -> int:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM documents WHERE project_id = ? AND status = 'ready'",
            (project_id,),
        ).fetchone()
        return row["n"]
    finally:
        conn.close()


def get_ready_document_pages(project_id: str) -> list[dict]:
    """Nur Seiten von Dokumenten mit status='ready' desselben Projekts (Prinzip III/IV)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT dp.document_id, d.filename, dp.page_number, dp.text
            FROM document_pages dp
            JOIN documents d ON d.id = dp.document_id
            WHERE d.project_id = ? AND d.status = 'ready'
            ORDER BY d.uploaded_at ASC, dp.page_number ASC
            """,
            (project_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# --- Nachrichten / Gespraechsverlauf --------------------------------------

def create_message(project_id: str, role: str, content: str, sources: list[dict] | None = None) -> dict:
    message_id = str(uuid.uuid4())
    created_at = _now()
    sources_json = json.dumps(sources or [])
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO messages (id, project_id, role, content, sources, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, project_id, role, content, sources_json, created_at),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "id": message_id,
        "project_id": project_id,
        "role": role,
        "content": content,
        "sources": sources or [],
        "created_at": created_at,
    }


def list_messages(project_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, role, content, sources, created_at
            FROM messages
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["sources"] = json.loads(item["sources"]) if item["sources"] else []
            result.append(item)
        return result
    finally:
        conn.close()
