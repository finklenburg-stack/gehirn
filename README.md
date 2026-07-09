# Dokumenten-QA

Ein lokales Web-Tool, mit dem du Projekte (z.B. pro CAS/Kurs) anlegst, PDF-Kursunterlagen
hochlädst und im Chat-Stil Fragen dazu stellst. Antworten werden ausschliesslich aus den
PDFs des aktiven Projekts erzeugt (über die Anthropic API) und enthalten eine
Quellenangabe (Dokument + Seite).

Details zur Spezifikation, Architektur und den Design-Entscheidungen:
[`specs/001-document-qa-projects/`](specs/001-document-qa-projects/).

## Voraussetzungen

- Python 3.11+
- Ein Anthropic-API-Key

## Setup

```bash
pip install -r requirements.txt

# API-Key lokal hinterlegen (wird nie committed, siehe .gitignore)
cp .env.example .env
# .env öffnen und ANTHROPIC_API_KEY=... eintragen

uvicorn src.main:app --reload
```

Die Web-Oberfläche ist danach unter <http://localhost:8000> erreichbar.

## Tests

```bash
pytest
```

Die meisten Tests laufen komplett offline. Zwei Tests in
`tests/integration/test_answer_quality.py` rufen echt die Anthropic API auf und werden
ohne gesetzten `ANTHROPIC_API_KEY` automatisch übersprungen:

```bash
ANTHROPIC_API_KEY=sk-ant-... pytest tests/integration/test_answer_quality.py
```

## Validierungsszenarien

Eine ausführliche, manuelle Checkliste (Projekt anlegen, Fragen stellen, Projekt-Isolation,
Folgefragen, Ladeanzeige, Fehlerfälle) findet sich in
[`specs/001-document-qa-projects/quickstart.md`](specs/001-document-qa-projects/quickstart.md).
