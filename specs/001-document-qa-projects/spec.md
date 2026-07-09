# Feature Specification: Projektbasierte Dokumenten-Fragebeantwortung

**Feature Branch**: `001-document-qa-projects`

**Created**: 2026-07-09

**Status**: Draft

**Input**: User description: "Ich will ein Tool bauen das mir anhand von Dokumenten eine Antwort auf spezifische Fragen gibt, z.B. mache ich ein CAS habe PDF vom Dozenten erhalten und will die Antworten nur anhand dieser PDF erhalten. Ich will verschiedene Projekte für verschiedene Themen also verschiedene CAS oder andere Sachen anlegen können und für jedes Projekt sollen nur die richtigen PDF verwendet werden. Das Tool soll über einen Anthropic API-Key die KI verwenden und mir so die richtige Antwort auf meine Frage gemäss diesen PDF liefern."

## Clarifications

### Session 2026-07-09

- Q: Über welche Zugriffsart/Interface soll der Nutzer mit dem Tool interagieren? → A: Lokale Web-Oberfläche im Browser (Formulare, Drag&Drop-Upload, Chat-Fenster)
- Q: Sollen Folgefragen sich auf vorherige Fragen/Antworten im selben Projekt beziehen können (Gesprächskontext)? → A: Ja, Chat mit Verlauf – Folgefragen beziehen sich auf den bisherigen Gesprächsverlauf im selben Projekt

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Projekt anlegen und PDFs zuordnen (Priority: P1)

Als Nutzer möchte ich ein neues Projekt (z.B. für ein bestimmtes CAS oder Thema) anlegen und diesem Projekt PDF-Dokumente zuordnen können, damit mein Kursmaterial thematisch getrennt organisiert ist.

**Why this priority**: Ohne ein Projekt mit zugeordneten Dokumenten kann keine sinnvolle Frage beantwortet werden. Das ist die Grundvoraussetzung für jeden weiteren Schritt.

**Independent Test**: Ein neues Projekt anlegen, ein oder mehrere PDFs hinzufügen und verifizieren, dass die Dokumente diesem Projekt zugeordnet und dort einsehbar sind.

**Acceptance Scenarios**:

1. **Given** noch kein Projekt existiert, **When** der Nutzer ein neues Projekt mit einem Namen anlegt, **Then** existiert ein leeres Projekt, dem Dokumente zugeordnet werden können.
2. **Given** ein bestehendes Projekt, **When** der Nutzer eine PDF-Datei per Drag&Drop oder Datei-Auswahl in der Web-Oberfläche zu diesem Projekt hinzufügt, **Then** ist die Datei diesem Projekt zugeordnet und in der Dokumentenliste des Projekts sichtbar.
3. **Given** ein bestehendes Projekt mit Dokumenten, **When** der Nutzer ein Dokument entfernt, **Then** wird dieses Dokument bei zukünftigen Fragen in diesem Projekt nicht mehr berücksichtigt.

---

### User Story 2 - Frage zu einem Projekt stellen und belegte Antwort erhalten (Priority: P1)

Als Nutzer möchte ich innerhalb eines Projekts eine Frage stellen und eine Antwort erhalten, die ausschliesslich auf den PDFs dieses Projekts basiert und die Quelle (Dokument, nach Möglichkeit Seite/Abschnitt) benennt, damit ich mich auf die Richtigkeit und Nachvollziehbarkeit der Antwort verlassen kann.

**Why this priority**: Dies ist der eigentliche Kernnutzen des Tools – die verlässliche, belegte Beantwortung von Fragen zum eigenen Kursmaterial.

**Independent Test**: In einem Projekt mit mindestens einem PDF eine Frage stellen, deren Antwort im Dokument steht, und prüfen, dass die Antwort korrekt ist und eine Quellenangabe enthält.

**Acceptance Scenarios**:

1. **Given** ein Projekt mit mindestens einem PDF, das die Antwort auf eine Frage enthält, **When** der Nutzer diese Frage stellt, **Then** liefert das Tool eine inhaltlich korrekte Antwort mit Angabe des Quelldokuments.
2. **Given** ein Projekt, dessen zugeordnete PDFs die gestellte Frage nicht beantworten, **When** der Nutzer diese Frage stellt, **Then** teilt das Tool explizit mit, dass die Antwort in den Unterlagen nicht gefunden wurde, statt eine Antwort zu erfinden.
3. **Given** ein Projekt ohne zugeordnete Dokumente, **When** der Nutzer eine Frage stellt, **Then** weist das Tool darauf hin, dass zuerst Dokumente hinzugefügt werden müssen.
4. **Given** eine bereits beantwortete Frage im aktiven Projekt, **When** der Nutzer eine Folgefrage stellt, die sich auf die vorherige Antwort bezieht, **Then** berücksichtigt das Tool den bisherigen Gesprächsverlauf bei der Beantwortung, bleibt dabei aber weiterhin ausschliesslich auf die PDFs des Projekts gestützt.

---

### User Story 3 - Zwischen Projekten wechseln ohne Vermischung (Priority: P2)

Als Nutzer möchte ich zwischen mehreren Projekten wechseln können, wobei Fragen in einem Projekt ausschliesslich anhand der PDFs genau dieses Projekts beantwortet werden, damit sich Inhalte verschiedener CAS/Themen nicht vermischen.

**Why this priority**: Wichtig für Nutzer mit mehreren parallelen Projekten, aber erst relevant, sobald mindestens zwei Projekte existieren – baut auf Story 1 und 2 auf.

**Independent Test**: Zwei Projekte mit unterschiedlichen PDFs anlegen, im ersten Projekt eine Frage stellen, deren Antwort nur im zweiten Projekt zu finden ist, und verifizieren, dass das Tool die Antwort nicht liefert bzw. korrekt meldet, dass sie im aktiven Projekt nicht vorhanden ist.

**Acceptance Scenarios**:

1. **Given** zwei Projekte mit unterschiedlichen, sich nicht überschneidenden PDFs, **When** der Nutzer im Projekt A eine Frage stellt, deren Antwort nur in einem PDF von Projekt B steht, **Then** liefert das Tool keine Antwort aus Projekt B, sondern meldet, dass die Information im aktiven Projekt fehlt.
2. **Given** mehrere Projekte, **When** der Nutzer das aktive Projekt wechselt, **Then** zeigt das Tool eindeutig an, welches Projekt gerade aktiv ist, bevor eine Frage gestellt wird.

---

### Edge Cases

- Was passiert, wenn ein hochgeladenes Dokument kein gültiges PDF ist oder beschädigt ist?
- Was passiert, wenn ein PDF nur aus gescannten Bildern ohne durchsuchbaren Text besteht (keine extrahierbare Textebene)?
- Was passiert, wenn der hinterlegte Anthropic-API-Key fehlt, ungültig ist oder das API-Guthaben/Limit erschöpft ist?
- Was passiert, wenn ein Projekt gelöscht wird, während es noch Dokumente enthält?
- Was passiert, wenn dieselbe Frage in einem Projekt mehrfach gestellt wird – liefert das Tool konsistent dieselbe Antwort?
- Was passiert, wenn ein einzelnes PDF sehr umfangreich ist (z.B. mehrere hundert Seiten)?
- Was passiert, wenn eine Folgefrage sich auf ein Dokument bezieht, das zwischenzeitlich aus dem Projekt entfernt wurde?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Nutzer MÜSSEN ein neues Projekt mit einem eindeutigen Namen anlegen können.
- **FR-002**: Nutzer MÜSSEN einem Projekt ein oder mehrere PDF-Dokumente zuordnen können.
- **FR-003**: Nutzer MÜSSEN die einem Projekt zugeordneten Dokumente einsehen und einzelne Dokumente wieder entfernen können.
- **FR-004**: System MUSS beim Beantworten einer Frage innerhalb eines Projekts ausschliesslich die PDFs verwenden, die genau diesem Projekt zugeordnet sind.
- **FR-005**: System MUSS bei jeder Antwort das/die Quelldokument(e) angeben, aus denen die Information stammt.
- **FR-006**: System MUSS explizit mitteilen, wenn die gestellte Frage anhand der zugeordneten Dokumente nicht beantwortet werden kann, statt eine Antwort ohne Dokumentbasis zu generieren.
- **FR-007**: System MUSS zur Erzeugung der Antworten die Anthropic API mit einem vom Nutzer bereitgestellten API-Key verwenden.
- **FR-008**: System MUSS den Anthropic-API-Key sicher entgegennehmen (z.B. Umgebungsvariable oder lokale, nicht versionierte Konfiguration) und darf ihn nicht in Logs oder Versionskontrolle offenlegen.
- **FR-009**: System MUSS den Nutzer verständlich informieren, wenn eine Frage ohne gültigen API-Key oder ohne zugeordnete Dokumente gestellt wird.
- **FR-010**: System MUSS mehrere Projekte parallel verwalten können, ohne dass Dokumente oder Antworten zwischen Projekten vermischt werden.
- **FR-011**: System MUSS erkennbar anzeigen, welches Projekt aktuell aktiv ist, bevor eine Frage beantwortet wird.
- **FR-012**: System MUSS den Nutzer informieren, wenn ein hochgeladenes Dokument kein verarbeitbares PDF ist (z.B. beschädigt oder ohne extrahierbaren Text).
- **FR-013**: System MUSS über eine lokale Web-Oberfläche im Browser bedienbar sein: Projekte verwalten und PDFs per Drag&Drop (oder Datei-Auswahl) hochladen sowie Fragen über ein Chat-artiges Eingabefeld stellen und die Antworten dort anzeigen.
- **FR-014**: System MUSS bei der Beantwortung einer Frage den bisherigen Gesprächsverlauf desselben Projekts als Kontext berücksichtigen, sodass Folgefragen sich auf vorherige Fragen/Antworten beziehen können, ohne die Grundregel (ausschliesslich Antworten aus den zugeordneten PDFs) zu verletzen.
- **FR-015**: System MUSS den Gesprächsverlauf pro Projekt sichtbar darstellen, damit der Nutzer nachvollziehen kann, worauf sich eine Folgefrage bezieht.

### Key Entities

- **Projekt**: Eine thematische Arbeitseinheit (z.B. ein CAS oder Kursthema) mit einem Namen; besitzt eine Menge zugeordneter Dokumente und dient als Kontext-Grenze für Fragen.
- **Dokument**: Eine PDF-Datei, die genau einem Projekt zugeordnet ist; dient als alleinige Wissensquelle für Fragen innerhalb dieses Projekts.
- **Frage/Antwort**: Eine vom Nutzer gestellte Frage innerhalb eines aktiven Projekts sowie die daraus resultierende Antwort inklusive Quellenangabe(n).
- **Gesprächsverlauf**: Die geordnete Abfolge von Frage/Antwort-Paaren innerhalb eines Projekts; dient als zusätzlicher Kontext für Folgefragen im selben Projekt und ist pro Projekt getrennt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ein Nutzer kann ein neues Projekt anlegen und ein PDF zuordnen in unter 2 Minuten.
- **SC-002**: Bei Fragen, deren Antwort eindeutig in den zugeordneten PDFs steht, liefert das Tool in mindestens 90% der Fälle eine inhaltlich korrekte, belegte Antwort.
- **SC-003**: Bei Fragen, deren Antwort nicht in den zugeordneten PDFs enthalten ist, meldet das Tool in 100% der Fälle, dass keine Antwort gefunden wurde, statt eine erfundene Antwort zu liefern.
- **SC-004**: Bei keinem Test wird eine Information aus einem anderen Projekt in die Antwort eines aktiven Projekts übernommen (0% Vermischung zwischen Projekten).
- **SC-005**: Jede gelieferte Antwort enthält eine nachvollziehbare Quellenangabe, die der Nutzer ohne technisches Vorwissen einem Dokument zuordnen kann.

## Assumptions

- Das Tool wird von einer einzelnen Person genutzt (kein Mehrbenutzer-/Rechte-System erforderlich).
- Projekte und Dokumente werden lokal bzw. in einem vom Nutzer kontrollierten Speicherort persistent abgelegt, sodass sie über mehrere Sitzungen hinweg erhalten bleiben.
- PDFs enthalten durchsuchbaren Text; OCR für gescannte Bilddokumente ist für die erste Version nicht zwingend erforderlich (kann als spätere Erweiterung betrachtet werden).
- Es gibt kein hartes Limit für Anzahl oder Grösse der PDFs pro Projekt in der ersten Version; sehr grosse Dokumente können die Antwortzeit verlängern.
- Antworten werden in der Sprache der gestellten Frage bzw. der Dokumente formuliert (i.d.R. Deutsch), ohne dass dies gesondert konfiguriert werden muss.
