"""Verifiziert SC-004 / Prinzip III (Projekt-Isolation): Inhalte eines
Projekts duerfen niemals in den Kontext oder die Antworten eines anderen
Projekts gelangen.

Laeuft komplett offline (keine Anthropic-API-Aufrufe noetig): Die
Isolation wird direkt auf der Ebene der Kontext-Zusammenstellung
(`build_document_context`) sowie ueber die REST-Endpunkte geprueft, die
tatsaechlich fuer die Grounding-Garantie verantwortlich sind.
"""

from src.core.claude_client import build_document_context
from tests.helpers import make_pdf_bytes


def _create_project_with_pdf(client, name: str, fact: str) -> str:
    response = client.post("/api/projects", json={"name": name})
    assert response.status_code == 201
    project_id = response.json()["id"]

    pdf_bytes = make_pdf_bytes([fact])
    upload = client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": ("fixture.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 202
    assert upload.json()["status"] == "ready"
    return project_id


def test_document_context_does_not_leak_across_projects(client):
    project_a = _create_project_with_pdf(client, "Isolation Projekt A", "Fact only in project A: Zephyrion.")
    project_b = _create_project_with_pdf(client, "Isolation Projekt B", "Fact only in project B: Quandalor.")

    context_a, _ = build_document_context(project_a)
    context_b, _ = build_document_context(project_b)

    assert "Zephyrion" in context_a
    assert "Quandalor" not in context_a

    assert "Quandalor" in context_b
    assert "Zephyrion" not in context_b


def test_document_list_does_not_leak_across_projects(client):
    project_a = _create_project_with_pdf(client, "Isolation Dokumentliste A", "irrelevant content A")
    project_b = _create_project_with_pdf(client, "Isolation Dokumentliste B", "irrelevant content B")

    docs_a = client.get(f"/api/projects/{project_a}/documents").json()
    docs_b = client.get(f"/api/projects/{project_b}/documents").json()

    assert len(docs_a) == 1
    assert len(docs_b) == 1
    assert docs_a[0]["id"] != docs_b[0]["id"]


def test_deleting_document_from_wrong_project_is_rejected(client):
    project_a = _create_project_with_pdf(client, "Isolation Loeschschutz A", "content A")
    project_b = _create_project_with_pdf(client, "Isolation Loeschschutz B", "content B")

    doc_b = client.get(f"/api/projects/{project_b}/documents").json()[0]

    response = client.delete(f"/api/projects/{project_a}/documents/{doc_b['id']}")
    assert response.status_code == 404

    still_there = client.get(f"/api/projects/{project_b}/documents").json()
    assert len(still_there) == 1


def test_message_history_does_not_leak_across_projects(client):
    project_a = _create_project_with_pdf(client, "Isolation Verlauf A", "content A")
    project_b = _create_project_with_pdf(client, "Isolation Verlauf B", "content B")

    # 409 no_documents wird nicht ausgeloest (Dokumente vorhanden), aber ohne
    # API-Key schlaegt der eigentliche Claude-Aufruf mit ai_unavailable fehl -
    # das reicht hier nicht zum Pruefen des Verlaufs. Stattdessen direkt
    # Nachrichten anlegen und die Trennung auf DB-Ebene pruefen.
    from src.storage import db

    db.create_message(project_a, "user", "Frage nur in Projekt A")
    db.create_message(project_b, "user", "Frage nur in Projekt B")

    history_a = client.get(f"/api/projects/{project_a}/messages").json()
    history_b = client.get(f"/api/projects/{project_b}/messages").json()

    assert [m["content"] for m in history_a] == ["Frage nur in Projekt A"]
    assert [m["content"] for m in history_b] == ["Frage nur in Projekt B"]
