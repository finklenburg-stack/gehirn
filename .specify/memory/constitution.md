<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first concrete version, replacing placeholder template)
- Added sections:
  - I. Einfachheit zuerst
  - II. Antworten ausschliesslich aus Quelldokumenten
  - III. Projekt-Isolation
  - IV. Nachvollziehbarkeit der Antworten
  - V. Sicherer Umgang mit dem API-Key
  - Technische Rahmenbedingungen
  - Entwicklungs-Workflow
  - Governance
- Removed sections: none (placeholders replaced with concrete content)
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (Constitution Check section is generic/dynamic, no edit needed)
  - ✅ .specify/templates/spec-template.md (no constitution-specific references found)
  - ✅ .specify/templates/tasks-template.md (no constitution-specific references found)
- Follow-up TODOs: none
-->

# Dokumenten-QA Constitution

## Core Principles

### I. Einfachheit zuerst
Jede Lösung MUSS so einfach wie möglich gehalten werden. Kein Feature, keine
Abstraktion und kein Technologie-Baustein wird eingeführt, bevor er
tatsächlich gebraucht wird (YAGNI). Ein einzelner, klar verständlicher Weg
von PDF-Upload über Frage bis Antwort hat Vorrang vor konfigurierbaren
Mehrwegen oder vorzeitiger Generalisierung.
**Begründung**: Das Tool wird von einer Einzelperson für den eigenen
Lernbedarf (z.B. CAS-Unterlagen) gebaut und gepflegt; Komplexität, die
niemand braucht, kostet nur Zeit und erhöht die Fehleranfälligkeit.

### II. Antworten ausschliesslich aus Quelldokumenten (NICHT VERHANDELBAR)
Antworten MÜSSEN ausschliesslich auf Basis der PDFs erzeugt werden, die dem
aktiven Projekt zugeordnet sind. Enthält keines der zugeordneten Dokumente
die benötigte Information, MUSS das Tool dies explizit mitteilen ("nicht in
den Unterlagen gefunden") statt eine Antwort aus allgemeinem KI-Wissen zu
erfinden.
**Begründung**: Der zentrale Zweck des Tools ist die verlässliche
Beantwortung von Fragen zu spezifischem Kursmaterial (z.B. CAS-Unterlagen);
erfundene oder aus Fremdwissen ergänzte Antworten würden dieses Ziel
untergraben und beim Lernen in die Irre führen.

### III. Projekt-Isolation
Jede fachliche Einheit (z.B. ein CAS, ein Kurs, ein Thema) wird als eigenes
Projekt angelegt. Eine Anfrage innerhalb eines Projekts DARF nur auf die
PDFs zugreifen, die genau diesem Projekt zugeordnet sind. Dokumente aus
anderen Projekten dürfen weder in den Kontext gelangen noch in Antworten
einfliessen.
**Begründung**: Nutzer verwalten mehrere thematisch getrennte Projekte
parallel; eine Vermischung von Inhalten verschiedener Kurse würde falsche
oder irreführende Antworten erzeugen.

### IV. Nachvollziehbarkeit der Antworten
Jede Antwort MUSS erkennen lassen, aus welchem Dokument (mindestens
Dateiname, nach Möglichkeit Seiten- oder Abschnittsangabe) die Information
stammt. Der Nutzer MUSS in der Lage sein, eine Antwort in der Originalquelle
zu überprüfen.
**Begründung**: Für Lernzwecke (z.B. Prüfungsvorbereitung) ist die
Rückverfolgbarkeit auf die Originalstelle im PDF wichtiger als eine kurze,
nicht überprüfbare Antwort.

### V. Sicherer Umgang mit dem API-Key
Der Anthropic-API-Key MUSS über Umgebungsvariablen oder eine lokale,
nicht versionierte Konfigurationsdatei bereitgestellt werden. Der Key DARF
niemals hartkodiert, geloggt oder in Git committed werden.
**Begründung**: Der API-Key ist ein persönliches, kostenpflichtiges
Zugangsmittel; ein versehentlicher Leak (z.B. durch Commit ins Repo) hätte
direkte finanzielle und sicherheitsrelevante Folgen.

## Technische Rahmenbedingungen

- Die KI-Antworten werden über die Anthropic API (Claude-Modelle) mit einem
  vom Nutzer bereitgestellten API-Key erzeugt.
- Quelldokumente sind PDF-Dateien, die einem Projekt zugeordnet werden.
- Projekte und ihre zugeordneten Dokumente sind persistent und sauber
  voneinander getrennt zu speichern (z.B. pro Projekt ein eigener
  Ordner/Namespace).
- Ein Wechsel auf einen anderen KI-Anbieter oder ein anderes Dateiformat als
  PDF erfordert ein explizites Amendment dieser Constitution, da er
  Grundannahmen von Prinzip II–V berührt.

## Entwicklungs-Workflow

- Jede neue Fähigkeit beginnt mit einer Spezifikation (`/speckit-specify`),
  bevor Code geschrieben wird; Spec-Driven Development über spec-kit ist
  verbindlich.
- Änderungen, die eines der Core Principles verletzen oder aufweichen
  würden (insbesondere II, III oder V), erfordern zuerst ein Amendment
  dieser Constitution samt Begründung, bevor sie umgesetzt werden dürfen.
- Vor der Implementierung (`/speckit-implement`) wird der "Constitution
  Check" aus dem Plan (`/speckit-plan`) gegen diese Prinzipien geprüft.

## Governance

Diese Constitution hat Vorrang vor allen anderen Praktiken, Vorlagen oder
Ad-hoc-Entscheidungen in diesem Projekt. Bei Widersprüchen zwischen dieser
Constitution und einer Spec, einem Plan oder Code gilt die Constitution.

Amendments (Änderungen an Prinzipien oder Sections) MÜSSEN:
1. schriftlich begründet werden (was ändert sich und warum),
2. eine Versionsanhebung gemäss Semantic Versioning erhalten
   (MAJOR = Prinzip entfernt/grundlegend neu definiert,
   MINOR = neues Prinzip/Section hinzugefügt,
   PATCH = Klarstellung/Formulierung ohne inhaltliche Änderung),
3. im Sync Impact Report am Dateikopf dokumentiert werden.

Jeder `/speckit-plan`-Durchlauf MUSS die Einhaltung dieser Prinzipien über
den "Constitution Check" prüfen; Abweichungen müssen dort explizit
begründet werden.

**Version**: 1.0.0 | **Ratified**: 2026-07-09 | **Last Amended**: 2026-07-09
