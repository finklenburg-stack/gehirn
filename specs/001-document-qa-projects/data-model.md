# Data Model: Projektbasierte Dokumenten-Fragebeantwortung

**Feature**: 001-document-qa-projects
**Date**: 2026-07-09

Abgeleitet aus den "Key Entities" in `spec.md` sowie den funktionalen
Anforderungen FR-001 bis FR-016. Persistiert in SQLite (siehe research.md
§3); Original-PDFs liegen zusätzlich als Dateien im Dateisystem.

## Entität: Projekt

Repräsentiert eine thematische Arbeitseinheit (z.B. ein CAS/Kurs) und dient
als Isolationsgrenze (Prinzip III).

| Feld | Typ | Regeln |
|---|---|---|
| `id` | TEXT (UUID) | Primärschlüssel |
| `name` | TEXT | Pflichtfeld, projektweit eindeutig (FR-001), nicht leer |
| `created_at` | TIMESTAMP | Automatisch gesetzt bei Erstellung |

**Beziehungen**: 1 Projekt → n Dokumente, 1 Projekt → n Nachrichten.

**Löschregel**: Wird ein Projekt gelöscht, werden alle zugeordneten
Dokumente (inkl. Dateien) und Nachrichten mitgelöscht (kaskadierend) – das
beantwortet den in spec.md offen benannten Edge Case "Projekt wird
gelöscht, während es noch Dokumente enthält".

## Entität: Dokument

Eine PDF-Datei, die genau einem Projekt zugeordnet ist (FR-002, FR-003).

| Feld | Typ | Regeln |
|---|---|---|
| `id` | TEXT (UUID) | Primärschlüssel |
| `project_id` | TEXT | Fremdschlüssel → Projekt, NOT NULL (erzwingt Prinzip III) |
| `filename` | TEXT | Ursprünglicher Dateiname, wie hochgeladen |
| `storage_path` | TEXT | Pfad zur Originaldatei unter `data/<project_id>/documents/` |
| `page_count` | INTEGER | Anzahl extrahierter Seiten, NULL solange Status `processing` |
| `status` | TEXT | `processing` \| `ready` \| `failed` (siehe Zustandsübergänge unten) |
| `error_message` | TEXT | Nur gesetzt, wenn `status = failed` (Grund, z.B. "kein extrahierbarer Text") – bedient FR-012 |
| `uploaded_at` | TIMESTAMP | Automatisch gesetzt |

**Zustandsübergänge**:

```text
processing → ready    (Textextraktion erfolgreich, ≥1 Seite mit Text)
processing → failed   (kein gültiges PDF, beschädigt, oder kein
                        extrahierbarer Text – FR-012, Edge Case "Scan ohne Textebene")
```

Nur Dokumente im Status `ready` werden als Kontext für Fragen verwendet
(FR-004).

## Entität: Dokumentseite

Feingranulare Ablage des extrahierten Textes, notwendig für
seitengenaue Quellenangaben (Prinzip IV).

| Feld | Typ | Regeln |
|---|---|---|
| `id` | TEXT (UUID) | Primärschlüssel |
| `document_id` | TEXT | Fremdschlüssel → Dokument, NOT NULL |
| `page_number` | INTEGER | 1-basiert |
| `text` | TEXT | Extrahierter Text dieser Seite (kann leer sein) |

**Constraint**: `(document_id, page_number)` eindeutig.

## Entität: Nachricht

Ein einzelner Eintrag im Gesprächsverlauf eines Projekts – entweder eine
Nutzerfrage oder eine System-/Assistenten-Antwort (FR-005, FR-014, FR-015).

| Feld | Typ | Regeln |
|---|---|---|
| `id` | TEXT (UUID) | Primärschlüssel |
| `project_id` | TEXT | Fremdschlüssel → Projekt, NOT NULL (erzwingt Prinzip III) |
| `role` | TEXT | `user` \| `assistant` |
| `content` | TEXT | Fragetext bzw. Antworttext, nicht leer |
| `sources` | TEXT (JSON) | Nur bei `role = assistant`: Liste von `{document_id, filename, page_number}` – leer, wenn "nicht in den Unterlagen gefunden" geantwortet wurde |
| `created_at` | TIMESTAMP | Automatisch gesetzt, bestimmt Reihenfolge im Gesprächsverlauf |

`sources` speichert `filename` bewusst redundant zum Zeitpunkt der Antwort
(kein Live-Join über `document_id`). Das beantwortet den Edge Case "Folgefrage
bezieht sich auf ein zwischenzeitlich entferntes Dokument" aus spec.md: Auch
nachdem ein Dokument gelöscht wurde, bleibt die historische Quellenangabe im
Gesprächsverlauf über den gespeicherten `filename` lesbar. Die Web-Oberfläche
MUSS `document_id`-Verweise, die auf kein mehr existierendes Dokument zeigen,
tolerant behandeln (Anzeige des gespeicherten Dateinamens mit Hinweis
"Dokument entfernt" statt eines Fehlers/toten Links).

**Gesprächsverlauf** (siehe spec.md Key Entities) ist keine eigene Tabelle,
sondern die nach `created_at` sortierte Liste aller `Nachricht`-Einträge
eines Projekts – wird für Folgefragen als Kontext mitgegeben (FR-014).

## Validierungsregeln (Zusammenfassung)

- `Projekt.name`: Pflicht, eindeutig, nicht leer.
- `Dokument`: MUSS einem existierenden Projekt zugeordnet sein; nur
  `.pdf`-Dateien werden akzeptiert (FR-012 prüft dies vor der Verarbeitung).
- `Nachricht.content`: Pflicht, nicht leer.
- Jede Datenbankabfrage für Dokumente/Nachrichten MUSS nach `project_id`
  gefiltert sein – es gibt keinen Abfragepfad, der projektübergreifend
  liest (Prinzip III, wird in `contracts/api.md` und den zugehörigen Tasks
  konkretisiert).
