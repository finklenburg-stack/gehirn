# Research: Projektbasierte Dokumenten-Fragebeantwortung

**Feature**: 001-document-qa-projects
**Date**: 2026-07-09

Dieses Dokument löst alle technischen Unklarheiten aus dem Technical Context
auf, bevor das Design (Phase 1) beginnt. Jede Entscheidung ist an den
Prinzipien aus `.specify/memory/constitution.md` ausgerichtet, insbesondere
"Einfachheit zuerst" (I) und "Sicherer Umgang mit dem API-Key" (V).

## 1. Sprache & Web-Framework

- **Decision**: Python 3.11+ mit FastAPI, ausgeliefert über `uvicorn`.
- **Rationale**: Ein einzelner Backend-Prozess kann sowohl die JSON-API als
  auch serverseitig gerenderte HTML-Seiten (Jinja2) ausliefern – kein
  separates Frontend-Build nötig. Python bietet ausgereifte, gut gewartete
  Bibliotheken für PDF-Textextraktion und das offizielle Anthropic-SDK.
- **Alternatives considered**: Node.js/Express mit React-SPA – verworfen,
  da ein SPA-Build-Prozess (Bundler, Node-Toolchain) zusätzliche Komplexität
  für ein Ein-Personen-Tool bedeutet, ohne einen Mehrwert für diesen
  Anwendungsfall zu bieten (verstösst gegen Prinzip I).

## 2. PDF-Textextraktion

- **Decision**: `pypdf` (reine Python-Bibliothek, MIT-Lizenz) zur
  seitenweisen Textextraktion.
- **Rationale**: Leichtgewichtig, wenige Abhängigkeiten, permissiv
  lizenziert, extrahiert Text pro Seite – das wird für die
  Seitenangabe in Quellennachweisen (Prinzip IV) direkt benötigt.
  Ausreichend, solange PDFs durchsuchbaren Text enthalten (siehe
  Annahme in spec.md: OCR ist für v1 nicht erforderlich).
- **Alternatives considered**: PyMuPDF/`fitz` (AGPL-Lizenz – für ein
  Tool, das ggf. später geteilt wird, ungünstig) und `pdfplumber`
  (mehr Abhängigkeiten, primär für Tabellenextraktion gedacht, die hier
  nicht gebraucht wird) – beide verworfen zugunsten der einfacheren,
  ausreichenden Lösung.

## 3. Persistenz

- **Decision**: SQLite über das Python-Standardmodul `sqlite3` (keine ORM)
  für Metadaten (Projekte, Dokumente, Nachrichten); Original-PDFs werden
  als Dateien im lokalen Dateisystem unter einem Projekt-Ordner abgelegt.
- **Rationale**: SQLite benötigt keinen separaten Datenbankserver, ist
  Teil der Python-Standardbibliothek und für Einzelnutzer-Datenmengen
  völlig ausreichend. Der reine Speicherort-Anspruch aus der Constitution
  ("pro Projekt eigener Ordner/Namespace") wird durch die Kombination aus
  Dateisystem-Ordner (PDFs) + `project_id`-Fremdschlüssel (Metadaten)
  erfüllt.
- **Alternatives considered**: SQLAlchemy-ORM – verworfen, da für die
  überschaubare Anzahl an Tabellen (Projekt, Dokument, Dokumentseite,
  Nachricht) eine zusätzliche Abstraktionsschicht keinen Mehrwert bietet
  (Prinzip I). PostgreSQL/anderer DB-Server – verworfen, da ein separater
  Serverprozess für ein lokales Ein-Personen-Tool unnötige
  Betriebskomplexität einführt.

## 4. Frage-Beantwortung ohne Vektor-Datenbank (v1)

- **Decision**: Für v1 wird der extrahierte Text aller einem Projekt
  zugeordneten Dokumente (mit eingebetteten Seitenmarkierungen, z.B.
  `[Dokument: skript.pdf, Seite 12]`) direkt als Kontext an die Anthropic
  API übergeben, zusammen mit dem bisherigen Gesprächsverlauf des Projekts.
  Das Modell wird über eine System-Instruktion angewiesen, ausschliesslich
  auf Basis dieses Kontexts zu antworten, Seitenmarkierungen für
  Quellenangaben zu nutzen und explizit "nicht in den Unterlagen gefunden"
  zu antworten, wenn die Information fehlt.
- **Rationale**: Erfüllt Prinzip II (nur Quelldokumente) und IV
  (Nachvollziehbarkeit) ohne die zusätzliche Komplexität einer
  Chunking-/Embedding-/Vektor-Suche-Pipeline. Claude-Modelle bieten ein
  grosses Kontextfenster, das für typische Kursunterlagen (Skripte,
  Foliensätze) ausreicht. Passt zur expliziten Annahme in spec.md, dass es
  in v1 kein hartes Grössenlimit gibt, aber sehr grosse Dokumente die
  Antwortzeit verlängern dürfen (Best-Effort, siehe SC-006/FR-016).
- **Alternatives considered**: Embeddings + Vektor-Datenbank (z.B. Chroma)
  für gezieltes Retrieval einzelner Textabschnitte – verworfen für v1, da
  dies zusätzliche Infrastruktur (Embedding-Modell-Aufrufe, Vektor-Index,
  Chunking-Strategie) erfordert, ohne dass die aktuelle Spec eine Grösse
  vorgibt, die dies zwingend nötig macht. Kann als spätere Erweiterung
  nachgerüstet werden, falls einzelne Projekte das Kontextfenster
  sprengen (das wäre dann ein neues Feature mit eigener Spec).
- **Ergänzung nach `/speckit-analyze`**: Da "kein hartes Grössenlimit"
  (Assumption in spec.md) sonst dazu führen könnte, dass der Kontext
  unbemerkt gekürzt wird, prüft `claude_client.py` vor dem API-Call die
  Gesamtgrösse des Kontexts gegen ein Tokenbudget und lehnt die Anfrage mit
  einer verständlichen Fehlermeldung ab (`context_too_large`, siehe
  contracts/api.md), statt still zu kürzen. Das schliesst v1 nicht gegen
  grosse Projekte ab, verhindert aber eine stillschweigende Verletzung von
  Prinzip II/IV. Volles Chunking/Retrieval bleibt weiterhin als spätere
  Erweiterung offen.

## 5. Anthropic-Anbindung & API-Key-Handling

- **Decision**: Offizielles `anthropic` Python-SDK; der API-Key wird
  ausschliesslich über die Umgebungsvariable `ANTHROPIC_API_KEY` gelesen,
  optional geladen aus einer lokalen `.env`-Datei via `python-dotenv`. Die
  `.env`-Datei wird über `.gitignore` von der Versionskontrolle
  ausgeschlossen.
- **Rationale**: Direkte Umsetzung von Prinzip V; das offizielle SDK
  übernimmt Retry-/Fehlerbehandlung für die API-Aufrufe.
- **Alternatives considered**: API-Key in einer Konfigurationsdatei im
  Klartext im Projektverzeichnis ohne `.gitignore`-Schutz – verworfen,
  da dies das Leak-Risiko aus Prinzip V direkt verletzen würde.

## 6. Frontend-Ansatz

- **Decision**: Serverseitig gerenderte Jinja2-Templates (Projektliste,
  Chat-Ansicht) plus minimales Vanilla-JavaScript für Drag&Drop-Upload und
  asynchrone Chat-Anfragen (`fetch`-Aufrufe gegen die JSON-API). Kein
  JS-Framework, kein Build-Schritt.
- **Rationale**: Erfüllt die Klärung "lokale Web-Oberfläche mit
  Drag&Drop-Upload und Chat-Fenster" aus der Spec mit minimalem
  technischem Overhead – passt zu Prinzip I.
- **Alternatives considered**: React/Vue-SPA – verworfen wegen
  Build-Tooling-Overhead für ein Ein-Personen-Tool ohne Bedarf an
  komplexer Client-State-Verwaltung.

## 7. Ladeanzeige während der Verarbeitung

- **Decision**: Der Chat-Endpunkt liefert die Antwort synchron nach
  Abschluss der Anthropic-Anfrage zurück; das Frontend zeigt ab dem
  Absenden der Frage bis zum Eintreffen der Antwort einen sichtbaren
  Lade-/Tipp-Indikator (kein Streaming in v1).
- **Rationale**: Erfüllt SC-006/FR-016 (sichtbare Rückmeldung, Best
  Effort, kein festes Zeitlimit) ohne die zusätzliche Komplexität einer
  Streaming-Response-Pipeline (Server-Sent Events/WebSockets).
- **Alternatives considered**: Streaming der Antwort token-weise – als
  spätere UX-Verbesserung denkbar, aber für v1 nicht nötig, da laut
  Klärung in spec.md eine sichtbare Ladeanzeige ausreicht (kein
  Zeitlimit gefordert).

## 8. Tests

- **Decision**: `pytest` (bereits als Dev-Dependency eingeplant) wird
  gezielt für zwei automatisierte Verifikations-Tests eingesetzt, die
  nicht verhandelbare bzw. statistisch definierte Anforderungen prüfen:
  Antwortqualität (`tests/integration/test_answer_quality.py`, SC-002/
  SC-003) und Projekt-Isolation (`tests/integration/test_project_isolation.py`,
  Prinzip III). Eine vollständige Contract-/Unit-Test-Suite (z.B. für
  jeden Endpunkt einzeln oder für `pdf_extraction.py`) ist für v1 NICHT
  eingeplant.
- **Rationale**: In spec.md wurden keine automatisierten Tests explizit
  gefordert (siehe tasks.md-Kopfzeile "Tests"); eine umfassende
  Test-Suite für ein Ein-Personen-Tool ohne diese Anforderung würde
  Prinzip I (Einfachheit zuerst) widersprechen. Die zwei genannten Tests
  sind die Ausnahme, weil sie nicht verhandelbare Constitution-Prinzipien
  (II/III/IV) bzw. statistische Erfolgskriterien (SC-002/SC-003) prüfen,
  die sich durch einmaliges manuelles Durchklicken (Quickstart) nicht
  verlässlich verifizieren lassen.
- **Alternatives considered**: Vollständige Contract-/Unit-Test-Suite von
  Anfang an – verworfen für v1 zugunsten der zwei gezielten
  Verifikations-Tests; kann bei Bedarf jederzeit ergänzt werden, da
  `pytest` + FastAPI `TestClient` als Tooling bereits vorhanden sind.

## 9. Antwortkonsistenz bei wiederholter Frage

- **Decision**: Es wird keine Wortidentität zwischen Antworten auf
  identische, wiederholt gestellte Fragen garantiert. Jede Anfrage wird
  unabhängig (ohne Antwort-Caching) anhand der aktuell zugeordneten
  Dokumente und des aktuellen Gesprächsverlaufs neu an die Anthropic API
  gestellt.
- **Rationale**: Ein Caching-Mechanismus für identische Fragen würde
  zusätzliche Komplexität (Cache-Invalidierung bei Dokumentänderungen,
  Schlüsselbildung über Gesprächsverlauf) einführen, ohne dass spec.md
  Wortidentität fordert – nur inhaltliche Korrektheit und Quellentreue
  (Prinzip II, FR-006) sind nicht verhandelbar und bleiben bei jeder
  Anfrage unabhängig gewährleistet.
- **Alternatives considered**: Antwort-Caching pro (Projekt, Frage,
  Dokumentstand) – verworfen für v1 als unnötige Komplexität (Prinzip I);
  kann bei Bedarf als spätere Optimierung nachgerüstet werden.

## Offene Punkte für spätere Iterationen (nicht v1)

- OCR für gescannte PDFs ohne Textebene.
- Embedding-/Vektor-basiertes Retrieval, falls einzelne Projekte das
  Kontextfenster des Modells überschreiten.
- Streaming von Antworten für schnellere wahrgenommene Reaktionszeit.
- Vollständige Contract-/Unit-Test-Suite über die zwei in Abschnitt 8
  genannten Verifikations-Tests hinaus.

Alle `NEEDS CLARIFICATION`-Punkte aus dem Technical Context sind durch die
obigen Entscheidungen aufgelöst.
