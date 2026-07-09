# Quickstart: Projektbasierte Dokumenten-Fragebeantwortung

**Feature**: 001-document-qa-projects
**Date**: 2026-07-09

Dieser Guide beschreibt, wie das Feature nach der Implementierung lokal
gestartet und end-to-end validiert wird. Details zu Endpunkten siehe
[contracts/api.md](./contracts/api.md), zum Datenmodell siehe
[data-model.md](./data-model.md).

## Voraussetzungen

- Python 3.11+
- Ein gültiger Anthropic-API-Key
- Mindestens ein Test-PDF mit durchsuchbarem Text (z.B. ein
  Kursskript-Ausschnitt)

## Setup

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# API-Key lokal hinterlegen (Datei wird NICHT committed, siehe .gitignore)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# Server starten
uvicorn src.main:app --reload
```

Danach ist die Web-Oberfläche unter `http://localhost:8000` erreichbar.

## Validierungsszenarien

Diese Szenarien spiegeln die Acceptance Scenarios aus `spec.md` und sollten
nach der Implementierung manuell (oder als Integrationstest) durchlaufen
werden.

### 1. Projekt anlegen & PDF zuordnen (User Story 1)

1. Neues Projekt z.B. "CAS Data Science" anlegen.
2. Ein Test-PDF per Drag&Drop hochladen.
3. **Erwartet**: Dokument erscheint mit Status "ready" in der
   Dokumentenliste des Projekts.

### 2. Belegte Antwort erhalten (User Story 2)

1. Im Projekt aus Schritt 1 eine Frage stellen, deren Antwort im PDF steht.
2. **Erwartet**: Antwort erscheint mit korrektem Inhalt und einer
   Quellenangabe (Dateiname + Seite, falls verfügbar).
3. Eine Frage stellen, deren Antwort NICHT im PDF steht.
4. **Erwartet**: Tool antwortet explizit, dass die Information in den
   Unterlagen nicht gefunden wurde – keine erfundene Antwort.

### 3. Projekt-Isolation (User Story 3)

1. Ein zweites Projekt "CAS Machine Learning" mit einem anderen Test-PDF
   anlegen.
2. Im ersten Projekt ("CAS Data Science") eine Frage stellen, deren Antwort
   nur im PDF des zweiten Projekts steht.
3. **Erwartet**: Keine Antwort aus dem zweiten Projekt; Tool meldet, dass
   die Information im aktiven Projekt fehlt.

### 4. Folgefragen mit Gesprächsverlauf

1. Im Projekt aus Schritt 1 eine Frage stellen und Antwort erhalten.
2. Eine Folgefrage stellen, die sich auf die vorherige Antwort bezieht
   (z.B. "Kannst du das genauer erklären?").
3. **Erwartet**: Die Folgefrage wird im Kontext der vorherigen Antwort
   sinnvoll beantwortet, weiterhin ausschliesslich gestützt auf die PDFs
   des Projekts.

### 5. Ladeanzeige während der Verarbeitung

1. Eine Frage stellen und währenddessen die UI beobachten.
2. **Erwartet**: Ein sichtbarer Lade-/Bearbeitungsindikator ist zu sehen,
   bis die Antwort eintrifft (kein eingefrorener Zustand).

### 6. Fehlerfälle

- PDF ohne extrahierbaren Text hochladen → Dokument wird als "failed"
  markiert, Nutzer erhält eine verständliche Meldung (FR-012).
- Frage stellen, ohne dass dem Projekt Dokumente zugeordnet sind → Hinweis,
  dass zuerst Dokumente hinzugefügt werden müssen (FR-009).
- Ungültiger/fehlender API-Key → verständliche Fehlermeldung statt
  Absturz (Edge Case aus spec.md).

## Nächster Schritt

Nach erfolgreicher Validierung dieser Szenarien: `/speckit-tasks` ausführen,
um die Implementierung in konkrete, abhängigkeitsgeordnete Tasks zu
zerlegen.
