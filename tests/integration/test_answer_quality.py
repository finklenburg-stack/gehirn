"""Verifiziert SC-002 (>=90% korrekte belegte Antworten) und SC-003 (100%
korrekte "nicht gefunden"-Meldung) stichprobenartig gegen echte
Anthropic-API-Aufrufe (siehe /speckit-analyze Finding G2).

Dieser Test verursacht echte API-Kosten und ist daher NICHT Teil der
Standard-Testsuite ohne Schluessel: er wird uebersprungen, solange kein
ANTHROPIC_API_KEY gesetzt ist. Mit gesetztem Schluessel:

    ANTHROPIC_API_KEY=sk-ant-... pytest tests/integration/test_answer_quality.py

Das Test-PDF wird selbst generiert (tests/helpers.make_pdf_bytes), es sind
keine externen Fixture-Dateien noetig.
"""

import os

import pytest

from tests.helpers import make_pdf_bytes

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Benoetigt einen echten ANTHROPIC_API_KEY fuer einen End-to-End-Test gegen die Anthropic API.",
)

KNOWN_FACT = "The capital of the fictional country Testland is Springfield."

# (Frage, erwarteter Teilstring in der Antwort) - Antwort MUSS im PDF stehen (SC-002)
KNOWN_ANSWER_QUESTIONS = [
    ("What is the capital of Testland?", "springfield"),
]

# Fragen, deren Antwort NICHT im PDF steht - Tool MUSS das explizit sagen (SC-003)
NOT_FOUND_QUESTIONS = [
    "What is the capital of France?",
    "How many employees does Google have?",
]

NOT_FOUND_PHRASE = "nicht in den unterlagen gefunden"


def _create_project_with_document(client, name: str) -> str:
    response = client.post("/api/projects", json={"name": name})
    assert response.status_code == 201
    project_id = response.json()["id"]

    pdf_bytes = make_pdf_bytes([KNOWN_FACT])
    upload = client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": ("fixture.pdf", pdf_bytes, "application/pdf")},
    )
    assert upload.status_code == 202
    assert upload.json()["status"] == "ready"
    return project_id


def test_known_answers_are_grounded(client):
    project_id = _create_project_with_document(client, "SC-002 Testprojekt")
    correct = 0
    for question, expected_substring in KNOWN_ANSWER_QUESTIONS:
        response = client.post(f"/api/projects/{project_id}/messages", json={"content": question})
        assert response.status_code == 201
        body = response.json()
        if expected_substring in body["content"].lower() and body["sources"]:
            correct += 1

    ratio = correct / len(KNOWN_ANSWER_QUESTIONS)
    assert ratio >= 0.9, f"SC-002: nur {ratio:.0%} der Fragen korrekt/belegt beantwortet"


def test_unanswerable_questions_are_declined(client):
    project_id = _create_project_with_document(client, "SC-003 Testprojekt")
    correct = 0
    for question in NOT_FOUND_QUESTIONS:
        response = client.post(f"/api/projects/{project_id}/messages", json={"content": question})
        assert response.status_code == 201
        body = response.json()
        if NOT_FOUND_PHRASE in body["content"].lower() and not body["sources"]:
            correct += 1

    ratio = correct / len(NOT_FOUND_QUESTIONS)
    assert ratio == 1.0, f"SC-003: nur {ratio:.0%} der unbeantwortbaren Fragen korrekt abgelehnt"
