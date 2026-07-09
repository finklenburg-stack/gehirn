from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Wird bei ungueltigen/beschaedigten PDFs oder fehlendem Text ausgeloest (FR-012)."""


def extract_pages(file_path: str) -> list[str]:
    """Extrahiert den Text jeder Seite eines PDFs.

    Wirft PDFExtractionError, wenn die Datei kein gueltiges PDF ist oder
    keine Seite durchsuchbaren Text enthaelt (z.B. gescanntes Dokument ohne
    Textebene, siehe Edge Case in spec.md).
    """
    try:
        reader = PdfReader(file_path)
    except Exception as exc:  # pypdf wirft je nach Fehlerart unterschiedliche Exceptions
        raise PDFExtractionError(f"Datei ist kein gueltiges PDF: {exc}") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(text)

    if not any(text.strip() for text in pages):
        raise PDFExtractionError(
            "Kein durchsuchbarer Text gefunden (moeglicherweise ein gescanntes "
            "Dokument ohne Textebene)."
        )

    return pages
