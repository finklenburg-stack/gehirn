# API-Contract: Projektbasierte Dokumenten-Fragebeantwortung

**Feature**: 001-document-qa-projects
**Date**: 2026-07-09

JSON-API, die vom serverseitig gerenderten Web-Frontend (`src/web/`) per
`fetch` konsumiert wird. Alle Endpunkte sind implizit auf einen einzelnen,
lokalen Nutzer beschränkt (keine Authentifizierung in v1, siehe
Assumptions in spec.md).

## Projekte

### `POST /api/projects`

Legt ein neues Projekt an (FR-001).

- **Request**: `{ "name": string }`
- **Response 201**: `{ "id": string, "name": string, "created_at": string }`
- **Response 409**: Name bereits vergeben – `{ "error": "name_taken" }`
- **Response 400**: Name leer/fehlt – `{ "error": "name_required" }`

### `GET /api/projects`

Listet alle Projekte (für die Projektauswahl in der UI).

- **Response 200**: `[ { "id", "name", "created_at", "document_count" } ]`

### `DELETE /api/projects/{project_id}`

Löscht ein Projekt inkl. aller Dokumente (Dateien + Metadaten) und
Nachrichten (kaskadierend, siehe data-model.md).

- **Response 204**: Erfolgreich gelöscht
- **Response 404**: Projekt existiert nicht

## Dokumente

### `POST /api/projects/{project_id}/documents`

Lädt eine PDF-Datei hoch und ordnet sie dem Projekt zu (FR-002).
Multipart-Upload.

- **Request**: `multipart/form-data` mit Feld `file` (PDF)
- **Response 202**: `{ "id": string, "filename": string, "status": "processing" }`
  (Extraktion läuft synchron vor der Response ab oder asynchron mit
  Status-Polling über `GET .../documents` – Umsetzungsdetail für Tasks)
- **Response 400**: Keine PDF-Datei – `{ "error": "invalid_file_type" }`
- **Response 404**: Projekt existiert nicht

### `GET /api/projects/{project_id}/documents`

Listet die einem Projekt zugeordneten Dokumente (FR-003).

- **Response 200**: `[ { "id", "filename", "page_count", "status", "error_message", "uploaded_at" } ]`

### `DELETE /api/projects/{project_id}/documents/{document_id}`

Entfernt ein Dokument aus dem Projekt (FR-003); danach wird es bei
zukünftigen Fragen nicht mehr berücksichtigt.

- **Response 204**: Erfolgreich entfernt
- **Response 404**: Dokument oder Projekt existiert nicht

## Fragen & Gesprächsverlauf

### `POST /api/projects/{project_id}/messages`

Stellt eine Frage im aktiven Projekt (FR-004 bis FR-006, FR-014, FR-016).
Der Server MUSS den Kontext ausschliesslich aus Dokumenten mit
`status = ready` desselben `project_id` sowie dem bisherigen
Gesprächsverlauf desselben Projekts aufbauen (Prinzip II, III).

- **Request**: `{ "content": string }`
- **Response 201**:
  ```json
  {
    "id": string,
    "role": "assistant",
    "content": string,
    "sources": [ { "document_id": string, "filename": string, "page_number": number } ],
    "created_at": string
  }
  ```
  `sources` ist ein leeres Array, wenn die Antwort "nicht in den
  Unterlagen gefunden" lautet (FR-006).
- **Response 400**: Frage leer – `{ "error": "content_required" }`
- **Response 409**: Projekt hat keine Dokumente im Status `ready` –
  `{ "error": "no_documents" }` (FR-009)
- **Response 404**: Projekt existiert nicht
- **Response 502**: Anthropic API nicht erreichbar/Key ungültig/Kontingent
  erschöpft – `{ "error": "ai_unavailable", "detail": string }` (Edge Case
  "API-Key fehlt/ungültig/Kontingent erschöpft")

Hinweis: Die Antwort wird nach vollständigem Abschluss der Anthropic-Anfrage
zurückgegeben (kein Streaming in v1, siehe research.md §7). Das Frontend
zeigt ab dem Absenden der Anfrage bis zum Eintreffen dieser Response einen
Lade-Indikator (FR-016).

### `GET /api/projects/{project_id}/messages`

Liefert den vollständigen Gesprächsverlauf eines Projekts, sortiert nach
`created_at` (FR-015).

- **Response 200**: `[ { "id", "role", "content", "sources", "created_at" } ]`
- **Response 404**: Projekt existiert nicht

## Fehlerformat (allgemein)

Alle Fehlerantworten folgen dem Schema `{ "error": string, "detail"?: string }`
mit einem stabilen, maschinenlesbaren `error`-Code (siehe oben) und
optional einer für den Nutzer verständlichen `detail`-Meldung, die das
Frontend direkt anzeigen kann.
