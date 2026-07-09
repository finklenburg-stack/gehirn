---

description: "Task list template for feature implementation"
---

# Tasks: Projektbasierte Dokumenten-Fragebeantwortung

**Input**: Design documents from `/specs/001-document-qa-projects/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: In spec.md wurden keine automatisierten Tests explizit gefordert; formale Test-First-Tasks pro Story wurden daher ausgelassen. Zwei gezielte Verifikations-Tasks sind trotzdem enthalten: Antwortqualität (T024, Phase 4) und Projekt-Isolation (T027, Phase 5) – beide adressieren nicht verhandelbare bzw. statistisch definierte Anforderungen aus spec.md (SC-002/SC-003 bzw. Prinzip III), die sich nicht allein durch manuelles Durchklicken verlässlich prüfen lassen.

**Organization**: Tasks sind nach User Story gruppiert (siehe spec.md), damit jede Story unabhängig implementiert und getestet werden kann.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Kann parallel ausgeführt werden (unterschiedliche Dateien, keine Abhängigkeiten)
- **[Story]**: Zugehörige User Story (US1, US2, US3)
- Dateipfade sind exakt angegeben

## Path Conventions

Single-Project-Layout gemäss plan.md: `src/`, `tests/`, `data/` im Repository-Root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Projekt-Grundgerüst anlegen

- [X] T001 Verzeichnisstruktur gemäss plan.md anlegen: `src/api/`, `src/core/`, `src/storage/`, `src/web/templates/`, `src/web/static/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `data/` (inkl. `__init__.py` in allen `src/`-Unterpaketen)
- [X] T002 Python-Projekt initialisieren: `pyproject.toml`/`requirements.txt` mit `fastapi`, `uvicorn`, `jinja2`, `anthropic`, `pypdf`, `python-dotenv`, `pytest` in Repository-Root
- [X] T003 [P] `.gitignore` um `.env`, `data/`, `__pycache__/`, `*.db` erweitern
- [X] T004 [P] `.env.example` mit Platzhalter `ANTHROPIC_API_KEY=` im Repository-Root anlegen

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Kerninfrastruktur, die vor JEDER User Story fertig sein muss

**⚠️ CRITICAL**: Keine User-Story-Arbeit beginnt, bevor diese Phase abgeschlossen ist

- [X] T005 SQLite-Schema (Tabellen `projects`, `documents`, `document_pages`, `messages` gemäss data-model.md) und Init-Funktion in `src/storage/db.py`
- [X] T006 [P] Konfigurations-Loader in `src/config.py` (liest `ANTHROPIC_API_KEY` aus Umgebungsvariable/`.env` via `python-dotenv`, wirft verständlichen Fehler bei fehlendem Key gemäss Prinzip V)
- [X] T007 [P] Dateisystem-Helper in `src/storage/files.py` (Projekt-Ordner unter `data/<project_id>/documents/` anlegen, PDF speichern/löschen, Projekt-Ordner beim Löschen entfernen)
- [X] T008 FastAPI-Grundgerüst in `src/main.py` (App-Instanz, Router-Einbindung, Jinja2-Template-Setup, Static-Files-Mount, DB-Init beim Start) (depends on T005)
- [X] T009 [P] Einheitliches Fehlerantwort-Schema (`{error, detail}` gemäss contracts/api.md) als Hilfsfunktion in `src/api/errors.py`

**Checkpoint**: Fundament steht – User-Story-Implementierung kann beginnen

---

## Phase 3: User Story 1 - Projekt anlegen und PDFs zuordnen (Priority: P1) 🎯 MVP

**Goal**: Nutzer kann ein Projekt anlegen, PDFs per Drag&Drop hochladen, die zugeordneten Dokumente einsehen und einzelne Dokumente wieder entfernen.

**Independent Test**: Neues Projekt anlegen, PDF hochladen, in Dokumentenliste sehen, wieder entfernen – ganz ohne dass Fragen gestellt werden.

### Implementation for User Story 1

- [X] T010 [P] [US1] Projekt-Datenzugriff in `src/storage/db.py`: `create_project`, `list_projects`, `get_project`, `delete_project` (kaskadierendes Löschen von Dokumenten/Nachrichten gemäss data-model.md) (depends on T005)
- [X] T011 [P] [US1] Seitenweise PDF-Textextraktion in `src/core/pdf_extraction.py` (nutzt `pypdf`; liefert Liste von Seiten-Texten oder wirft Fehler bei ungültigem/textlosem PDF)
- [X] T012 [US1] Dokument-Datenzugriff in `src/storage/db.py`: `create_document`, `list_documents`, `update_document_status`, `save_document_pages`, `delete_document` (depends on T010, T011)
- [X] T013 [US1] Endpunkte `POST /api/projects`, `GET /api/projects`, `DELETE /api/projects/{project_id}` in `src/api/projects.py` gemäss contracts/api.md (Namens-Pflicht/-Eindeutigkeit, Fehlercodes `name_required`/`name_taken`) (depends on T010, T009)
- [X] T014 [US1] Endpunkte `POST/GET/DELETE /api/projects/{project_id}/documents` in `src/api/documents.py` (Multipart-Upload, ruft `pdf_extraction`, `files.py`, `db.py` auf, setzt Status `processing`→`ready`/`failed`) (depends on T007, T011, T012, T009)
- [X] T015 [US1] Web-Oberfläche Projektübersicht + Upload in `src/web/templates/projects.html` und `src/web/static/upload.js` (Projekt anlegen, PDFs per Drag&Drop hochladen, Dokumentenliste mit Status anzeigen/entfernen) (depends on T013, T014)
- [X] T016 [US1] Validierung ergänzen: nur `.pdf`-Dateien akzeptieren, verständliche Fehlermeldung bei ungültigem/beschädigtem Dokument (FR-012) in `src/api/documents.py`

**Checkpoint**: User Story 1 ist eigenständig nutzbar und testbar (Projekte + Dokumentenverwaltung, ohne Frage-Antwort-Funktion)

---

## Phase 4: User Story 2 - Frage stellen und belegte Antwort erhalten (Priority: P1)

**Goal**: Nutzer stellt im aktiven Projekt eine Frage über ein Chat-Fenster und erhält eine Antwort, die ausschliesslich auf den projekteigenen PDFs basiert (mit Quellenangabe) oder eine ehrliche Fehlanzeige, inklusive Berücksichtigung des bisherigen Gesprächsverlaufs, einer sichtbaren Ladeanzeige und einer verständlichen Fehlermeldung statt stiller Kürzung, wenn der Kontext zu gross für das Modell wird.

**Independent Test**: In einem Projekt mit mindestens einem verarbeiteten PDF (aus US1) eine Frage stellen, deren Antwort im PDF steht → belegte Antwort; Frage ohne Antwort im PDF → "nicht gefunden"; Folgefrage, die sich auf die vorherige Antwort bezieht → sinnvoll im Kontext beantwortet; ein Testset aus bekannten Frage/Antwort-Paaren bestätigt die geforderte Trefferquote (SC-002/SC-003).

### Implementation for User Story 2

- [ ] T017 [P] [US2] Nachrichten-Datenzugriff in `src/storage/db.py`: `create_message`, `list_messages(project_id)` sortiert nach `created_at` (depends on T005)
- [ ] T018 [US2] Prompt-/Kontextaufbau und Anthropic-Anbindung in `src/core/claude_client.py`: baut System-Instruktion + Dokumentkontext (Seiten aus `document_pages` mit Seitenmarkierungen, nur Dokumente mit Status `ready`) + Gesprächsverlauf zusammen, ruft `anthropic`-SDK auf, parst Antworttext und Quellenangaben; System-Instruktion erzwingt explizit "nicht in den Unterlagen gefunden" statt erfundener Antworten (Prinzip II, FR-006); fängt Authentifizierungs-/Rate-Limit-/Verbindungsfehler des SDK ab und mappt sie auf den Fehlercode `ai_unavailable` (FR-009) (depends on T012, T017, T006)
- [ ] T019 [US2] Kontextgrössen-Prüfung in `src/core/claude_client.py`: vor dem Anthropic-API-Call die Gesamtlänge des zusammengestellten Kontexts (Dokumenttext + Gesprächsverlauf) gegen ein konfigurierbares Tokenbudget prüfen; bei Überschreitung KEINE stille Kürzung vornehmen, sondern den Fehlercode `context_too_large` mit verständlicher Meldung zurückgeben (schützt Prinzip II/IV vor unbemerkt unvollständigem Kontext, adressiert Edge Case "sehr umfangreiches PDF" und contracts/api.md Response 413) (depends on T018)
- [ ] T020 [US2] Gesprächsverlauf-Zusammenstellung in `src/core/conversation.py`: liefert den bisherigen Verlauf eines Projekts in einem für `claude_client.py` verwendbaren Format (FR-014, FR-015) (depends on T017)
- [ ] T021 [US2] Endpunkte `POST/GET /api/projects/{project_id}/messages` in `src/api/chat.py` gemäss contracts/api.md (Fehlercodes `content_required`, `no_documents`, `ai_unavailable`, `context_too_large`) (depends on T018, T019, T020, T009)
- [ ] T022 [US2] Chat-Oberfläche in `src/web/templates/chat.html` und `src/web/static/chat.js` (Frage-Eingabefeld, Anzeige Gesprächsverlauf inkl. Quellenangaben, sichtbarer Lade-/Bearbeitungsindikator zwischen Absenden und Antwort gemäss FR-016, verständliche Anzeige bei `context_too_large`; zeigt gespeicherte Quellenangaben aus `sources` auch dann korrekt an, wenn das referenzierte Dokument zwischenzeitlich entfernt wurde – Anzeige des gespeicherten Dateinamens mit Hinweis "Dokument entfernt" statt Fehler/totem Link, siehe data-model.md) (depends on T021)
- [ ] T023 [US2] Fehlerfall "keine Dokumente im Projekt" behandeln: verständlicher Hinweis in Chat-Oberfläche statt Frage-Eingabe ins Leere laufen zu lassen (FR-009) (depends on T021, T022)
- [ ] T024 [US2] Antwortqualitäts-Verifikation in `tests/integration/test_answer_quality.py`: kleines Set von Testfragen mit bekannter, im PDF vorhandener Antwort sowie Testfragen ohne Antwort im PDF definieren und gegen den Chat-Endpunkt (T021) laufen lassen, um SC-002 (≥90% korrekte belegte Antworten) und SC-003 (100% korrekte "nicht gefunden"-Meldung) stichprobenartig und wiederholbar zu verifizieren (depends on T015, T021)

**Checkpoint**: User Story 1 UND 2 funktionieren zusammen als nutzbares MVP (Projekt anlegen, PDFs hochladen, Fragen stellen und belegte Antworten mit Verlauf erhalten, inkl. Absicherung gegen zu grosse Kontexte und Qualitäts-Stichprobe)

---

## Phase 5: User Story 3 - Zwischen Projekten wechseln ohne Vermischung (Priority: P2)

**Goal**: Nutzer kann zwischen mehreren Projekten wechseln; Fragen werden garantiert nur anhand der PDFs des jeweils aktiven Projekts beantwortet, das aktive Projekt ist in der UI erkennbar.

**Independent Test**: Zwei Projekte mit unterschiedlichen, nicht überschneidenden PDFs anlegen; im ersten Projekt eine Frage stellen, deren Antwort nur im zweiten Projekt steht → keine Antwort aus dem zweiten Projekt, korrekte Fehlanzeige; aktives Projekt ist in der Oberfläche eindeutig sichtbar.

### Implementation for User Story 3

- [ ] T025 [P] [US3] Sichtbare Anzeige und Auswahl des aktiven Projekts in `src/web/templates/base.html` (Navigationsleiste/Projektauswahl, wird von `projects.html` und `chat.html` verwendet) (depends on T015)
- [ ] T026 [US3] Isolations-Review: alle Datenzugriffe in `src/storage/db.py` und Endpunkte in `src/api/documents.py`, `src/api/chat.py` daraufhin prüfen/härten, dass ausnahmslos nach `project_id` gefiltert wird und kein Pfad projektübergreifend liest (Prinzip III) (depends on T012, T017, T018, T021)
- [ ] T027 [US3] Verifikation der Projekt-Isolation in `tests/integration/test_project_isolation.py`: zwei Projekte mit unterschiedlichen Test-PDFs anlegen, Cross-Projekt-Frage stellen, sicherstellen dass keine fremden Inhalte in Kontext/Antwort/Quellenangaben gelangen (siehe quickstart.md Szenario 3) (depends on T026)

**Checkpoint**: Alle drei User Stories sind einzeln und im Zusammenspiel funktionsfähig

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verbesserungen, die mehrere User Stories betreffen

- [ ] T028 [P] Logging-Durchsicht: sicherstellen, dass der Anthropic-API-Key in keiner Log-Ausgabe erscheint (Prinzip V) in `src/config.py` und `src/core/claude_client.py`
- [ ] T029 [P] `README.md` im Repository-Root mit Kurzfassung der Setup-/Start-Anleitung aus `specs/001-document-qa-projects/quickstart.md`
- [ ] T030 Vollständige Quickstart-Validierung: alle 6 Szenarien aus `specs/001-document-qa-projects/quickstart.md` manuell durchlaufen
- [ ] T031 [P] `pyproject.toml`/`requirements.txt` finalisieren (Versionsangaben prüfen, ungenutzte Abhängigkeiten entfernen)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Keine Abhängigkeiten – kann sofort starten
- **Foundational (Phase 2)**: Abhängig von Setup – blockiert alle User Stories
- **User Story 1 (Phase 3)**: Abhängig von Foundational
- **User Story 2 (Phase 4)**: Abhängig von Foundational; nutzt Dokumente/Status aus US1 zur Laufzeit und hat eine Datenschema-Abhängigkeit zu T012 (Dokument-/Seiten-Tabellen aus US1); API-Endpunkte und UI von US2 sind davon unabhängig entwickelbar
- **User Story 3 (Phase 5)**: Abhängig von Foundational sowie den in US1/US2 geschaffenen Datenzugriffs- und Endpunktfunktionen, die gehärtet werden
- **Polish (Phase 6)**: Abhängig vom Abschluss der gewünschten User Stories

### User Story Dependencies

- **User Story 1 (P1)**: Keine Abhängigkeit zu anderen Stories – eigenständig testbar
- **User Story 2 (P1)**: Für einen sinnvollen End-to-End-Test wird mindestens ein Dokument aus US1 benötigt; ausserdem hat T018 eine Datenschema-Abhängigkeit zu T012 (US1). API-Endpunkte, Prompt-Aufbau und UI sind darüber hinaus unabhängig
- **User Story 3 (P2)**: Baut auf den Datenzugriffs-/Endpunktfunktionen aus US1 und US2 auf (Isolations-Härtung), daher sinnvollerweise nach US1/US2 umzusetzen

### Within Each User Story

- Datenzugriff (Storage) vor Services/Core-Logik
- Core-Logik vor API-Endpunkten
- API-Endpunkte vor UI/Templates
- Story ist abgeschlossen, bevor die nächste Priorität begonnen wird (bei sequenzieller Umsetzung)

### Parallel Opportunities

- T003, T004 (Setup) parallel
- T006, T007, T009 (Foundational) parallel, nachdem T005 steht
- T010, T011 (US1) parallel
- T017 (US2) kann parallel zu US1-Tasks starten, sobald Foundational steht
- T025 (US3) kann parallel zu T026/T027 vorbereitet werden

---

## Parallel Example: User Story 1

```bash
# Datenzugriff und PDF-Extraktion für User Story 1 parallel starten:
Task: "Projekt-Datenzugriff in src/storage/db.py"
Task: "Seitenweise PDF-Textextraktion in src/core/pdf_extraction.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2)

1. Phase 1: Setup abschliessen
2. Phase 2: Foundational abschliessen (blockiert alles andere)
3. Phase 3: User Story 1 abschliessen → Projekte/PDFs funktionieren eigenständig
4. Phase 4: User Story 2 abschliessen (inkl. T019 Kontextgrössen-Prüfung und T024 Antwortqualitäts-Verifikation) → **MVP erreicht**: Kernnutzen (belegte Antworten aus eigenen PDFs) ist nutzbar und stichprobenartig verifiziert
5. **STOPPEN und VALIDIEREN**: Quickstart-Szenarien 1, 2, 4, 5, 6 durchlaufen

### Incremental Delivery

1. Setup + Foundational → Fundament steht
2. User Story 1 → eigenständig testbar (Projektverwaltung)
3. User Story 2 → MVP nutzbar (Kernnutzen: belegte Antworten, gegen Kontextüberlauf abgesichert, qualitativ verifiziert)
4. User Story 3 → Mehrprojekt-Nutzung sauber abgesichert (Quickstart-Szenario 3)
5. Polish → Feinschliff, Dokumentation, vollständige Quickstart-Validierung

---

## Notes

- [P] Tasks = unterschiedliche Dateien, keine Abhängigkeiten untereinander
- [Story]-Label ordnet jede Task eindeutig einer User Story zu
- Nach jeder abgeschlossenen Task committen (siehe bisherige Commit-Praxis in diesem Repo)
- An jedem Checkpoint die zugehörige(n) Quickstart-Szenarien manuell verifizieren
- Vermeiden: Cross-Story-Abhängigkeiten, die die unabhängige Testbarkeit der Stories brechen
