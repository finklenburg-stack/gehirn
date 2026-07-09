"""Erzeugt minimale, gueltige PDF-Dateien mit bekanntem Text - ganz ohne
externe PDF-Generierungsbibliothek (Prinzip I: keine zusaetzliche
Abhaengigkeit nur fuer Tests). Wird von den Verifikations-Tests (T024,
T027) sowie fuer manuelle Smoke-Tests verwendet.
"""


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_pdf_bytes(pages: list[str]) -> bytes:
    """Baut ein minimales, korrektes PDF mit einer Textzeile pro Seite."""
    n_pages = len(pages)
    font_obj_num = 3 + n_pages * 2

    body_objs: list[tuple[int, bytes]] = []
    kids: list[int] = []
    obj_num = 3
    for text in pages:
        page_num = obj_num
        content_num = obj_num + 1
        obj_num += 2
        kids.append(page_num)

        content_bytes = f"BT /F1 18 Tf 72 700 Td ({_escape_pdf_text(text)}) Tj ET".encode("latin-1")
        content_stream = (
            f"{content_num} 0 obj<</Length {len(content_bytes)}>>stream\n".encode("latin-1")
            + content_bytes
            + b"\nendstream endobj\n"
        )
        page_dict = (
            f"{page_num} 0 obj<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 {font_obj_num} 0 R>>>>"
            f"/MediaBox[0 0 612 792]/Contents {content_num} 0 R>>endobj\n"
        ).encode("latin-1")
        body_objs.append((page_num, page_dict))
        body_objs.append((content_num, content_stream))

    catalog = b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    kids_str = " ".join(f"{k} 0 R" for k in kids)
    pages_obj = f"2 0 obj<</Type/Pages/Kids[{kids_str}]/Count {n_pages}>>endobj\n".encode("latin-1")
    font_obj = f"{font_obj_num} 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n".encode(
        "latin-1"
    )

    all_objs = sorted([(1, catalog), (2, pages_obj), *body_objs, (font_obj_num, font_obj)])

    buf = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}
    for num, data in all_objs:
        offsets[num] = len(buf)
        buf.extend(data)

    xref_start = len(buf)
    max_num = all_objs[-1][0]
    buf.extend(f"xref\n0 {max_num + 1}\n".encode("latin-1"))
    buf.extend(b"0000000000 65535 f \n")
    for num in range(1, max_num + 1):
        off = offsets.get(num, 0)
        buf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
    buf.extend(f"trailer<</Size {max_num + 1}/Root 1 0 R>>\n".encode("latin-1"))
    buf.extend(f"startxref\n{xref_start}\n%%EOF".encode("latin-1"))
    return bytes(buf)
