# Implementation Plan: Projektbasierte Dokumenten-Fragebeantwortung

**Branch**: `001-document-qa-projects` | **Date**: 2026-07-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-document-qa-projects/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Ein lokal betriebenes Web-Tool, mit dem eine einzelne Person Projekte (z.B.
pro CAS/Kurs) anlegt, PDF-Kursunterlagen per Drag&Drop hochlädt und im
Chat-Stil Fragen stellt. Antworten werden ausschliesslich aus den PDFs des
aktiven Projekts erzeugt (über die Anthropic API), enthalten eine
Quellenangabe (Dokument + möglichst Seite) und berücksichtigen den
bisherigen Gesprächsverlauf desselben Projekts. Technischer Ansatz: ein
einzelner Python/FastAPI-Prozess liefert sowohl JSON-API als auch
serverseitig gerenderte Web-Oberfläche aus; PDF-Text wird pro Seite
extrahiert und direkt (ohne Vektor-Datenbank) als Kontext an Claude
übergeben.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, uvicorn, Jinja2, `anthropic` (offizielles
SDK), `pypdf`, `python-dotenv`; `pytest` als Dev-Dependency

**Storage**: SQLite (Python-Standardmodul `sqlite3`, keine ORM) für
Projekte/Dokumente/Nachrichten; Original-PDFs als Dateien im lokalen
Dateisystem unter `data/<project-id>/documents/`

**Testing**: `pytest` + FastAPI `TestClient` für Contract-/Integrationstests,
einfache Unit-Tests für PDF-Extraktion und Prompt-Aufbau

**Target Platform**: Lokaler Rechner (Linux/macOS/Windows), Zugriff über
Browser via `http://localhost`

**Project Type**: Web-Anwendung – einzelner Backend-Prozess mit
servergerenderter Oberfläche (kein separates Frontend-Build)

**Performance Goals**: Best Effort ohne feste Zeitvorgabe für eine Antwort;
sichtbare Ladeanzeige während der Verarbeitung (siehe SC-006/FR-016)

**Constraints**: API-Key nie im Code/Log/Git (Prinzip V); Antworten
ausschliesslich aus den PDFs des aktiven Projekts (Prinzip II); keine
Vermischung von Inhalten zwischen Projekten (Prinzip III); jede Antwort mit
nachvollziehbarer Quellenangabe (Prinzip IV)

**Scale/Scope**: Einzelnutzer; wenige bis einige Dutzend Projekte parallel;
PDFs bis zu mehreren hundert Seiten pro Projekt (siehe research.md für die
Entscheidung gegen eine Vektor-Datenbank in v1); Gesprächsverlauf pro
Projekt wird vollständig gespeichert (kein automatisches Löschen in v1)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Prinzip | Gate | Bewertung |
|---|---|---|
| I. Einfachheit zuerst | Kein unnötiges Framework/Infrastruktur | PASS – Einzelprozess, SQLite statt DB-Server, kein Vektor-Store, kein Frontend-Build (siehe research.md) |
| II. Antworten ausschliesslich aus Quelldokumenten | Prompt-Kontext enthält ausschliesslich Text der projekteigenen Dokumente + Gesprächsverlauf; System-Instruktion verbietet Fremdwissen | PASS – siehe research.md §4, wird in data-model.md/contracts konkretisiert |
| III. Projekt-Isolation | Jede Datenbank-/Dateisystem-Abfrage ist zwingend nach `project_id` gescoped | PASS – Schema in data-model.md erzwingt Fremdschlüssel `project_id` auf allen relevanten Tabellen |
| IV. Nachvollziehbarkeit | Seitenbezogene Extraktion + Quellenangabe in jeder Antwort | PASS – `pypdf`-Extraktion pro Seite, Quellen werden strukturiert mit der Antwort gespeichert (siehe data-model.md) |
| V. Sicherer Umgang mit dem API-Key | Key nur via Umgebungsvariable/`.env`, nie committed | PASS – `.env` wird in `.gitignore` aufgenommen, Key wird nie geloggt |

**Ergebnis**: Keine Verstösse. Alle Gates bestehen sowohl vor Phase 0 als
auch nach dem Phase-1-Design (siehe Re-Check unten).

### Re-Check nach Phase 1 (Design)

Nach Erstellung von `data-model.md` und `contracts/api.md` bestätigt: Kein
Endpunkt und keine Tabelle umgeht die Projekt-Isolation (III) oder die
Quellenpflicht (IV); der Chat-Endpunkt-Contract erzwingt sowohl
Kontext-Grounding (II) als auch Quellenangaben (IV) auf Schnittstellenebene.
Keine Complexity-Tracking-Einträge nötig.

## Project Structure

### Documentation (this feature)

```text
specs/001-document-qa-projects/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── main.py                 # FastAPI-App-Einstiegspunkt
├── config.py                # Laden von ANTHROPIC_API_KEY aus Env/.env
├── api/
│   ├── projects.py          # Projekt anlegen/auflisten/löschen
│   ├── documents.py         # PDF hochladen/auflisten/entfernen
│   └── chat.py               # Frage stellen, Gesprächsverlauf abrufen
├── core/
│   ├── pdf_extraction.py     # Seitenweise Textextraktion (pypdf)
│   ├── claude_client.py      # Anthropic-Anbindung, Prompt-/Kontextaufbau
│   └── conversation.py       # Gesprächsverlauf-Zusammenstellung pro Projekt
├── storage/
│   ├── db.py                  # SQLite-Schema & Zugriff
│   └── files.py                # Ablage/Zugriff auf PDF-Dateien pro Projekt
└── web/
    ├── templates/               # Jinja2-Templates (Projektübersicht, Chat)
    └── static/                   # CSS + minimales Vanilla-JS (Upload, Chat-Fetch)

tests/
├── contract/                     # API-Endpunkt-Contract-Tests
├── integration/                   # End-to-End-Szenarien je User Story
└── unit/                           # PDF-Extraktion, Prompt-Aufbau, Isolation

data/                                # Laufzeitdaten, nicht versioniert (.gitignore)
└── <project-id>/
    └── documents/                    # Original-PDFs des Projekts
```

**Structure Decision**: Einzelnes Python-Projekt (Option "Single project"),
kein separates Frontend-Repository/Build. FastAPI liefert sowohl die
JSON-API (`src/api/`) als auch die serverseitig gerenderte Web-Oberfläche
(`src/web/`) aus demselben Prozess aus – konsistent mit Prinzip I
(Einfachheit zuerst) und der Klärung "lokale Web-Oberfläche" aus spec.md.

## Complexity Tracking

*Nicht anwendbar – der Constitution Check hat keine Verstösse ergeben, die
eine Rechtfertigung erfordern.*
