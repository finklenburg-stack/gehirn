import re

import anthropic

from src.config import ANTHROPIC_MODEL, MAX_CONTEXT_CHARS, MissingAPIKeyError, get_anthropic_api_key
from src.core.conversation import get_history_for_prompt
from src.storage import db

SYSTEM_PROMPT_TEMPLATE = """Du beantwortest Fragen ausschliesslich auf Basis der folgenden \
Dokumentauszuege aus dem Projekt "{project_name}". Verwende KEIN externes oder \
allgemeines Wissen, auch wenn du die Antwort kennst.

Regeln:
1. Wenn die Antwort eindeutig in den Dokumenten steht, antworte klar und korrekt. \
Belege JEDE Aussage direkt im Text mit einer Quellenangabe im exakten Format \
[Quelle: <Dateiname>, Seite <Seitenzahl>].
2. Wenn die Antwort NICHT in den Dokumenten enthalten ist, antworte ausschliesslich \
mit: "Ich habe dazu keine Antwort in den Unterlagen gefunden." Erfinde in diesem Fall \
keine Antwort und keine Quellenangabe.
3. Antworte in der Sprache der Frage.

Dokumente:
{context}
"""

SOURCE_PATTERN = re.compile(r"\[Quelle:\s*([^,\]]+),\s*Seite\s*(\d+)\s*\]")


class ClaudeClientError(Exception):
    pass


class ContextTooLargeError(ClaudeClientError):
    pass


class AIUnavailableError(ClaudeClientError):
    pass


def build_document_context(project_id: str) -> tuple[str, dict[str, str]]:
    """Baut den Dokumentkontext ausschliesslich aus Seiten von Dokumenten mit
    status='ready' desselben Projekts auf (Prinzip II, III) und liefert eine
    Zuordnung filename -> document_id fuer die Quellenangaben-Aufloesung.
    """
    pages = db.get_ready_document_pages(project_id)
    filename_to_document_id: dict[str, str] = {}
    blocks: list[str] = []
    current_doc = None
    for row in pages:
        filename_to_document_id[row["filename"]] = row["document_id"]
        if row["filename"] != current_doc:
            blocks.append(f"\n=== Dokument: {row['filename']} ===")
            current_doc = row["filename"]
        blocks.append(f"--- Seite {row['page_number']} ---\n{row['text']}")
    return "\n".join(blocks), filename_to_document_id


def _estimate_size(*parts: str) -> int:
    return sum(len(p) for p in parts)


def ask_question(project_id: str, project_name: str, question: str) -> dict:
    context, filename_to_document_id = build_document_context(project_id)
    history = get_history_for_prompt(project_id)
    history_text = "\n".join(m["content"] for m in history)

    if _estimate_size(context, history_text, question) > MAX_CONTEXT_CHARS:
        raise ContextTooLargeError(
            "Die Dokumente und der Gespraechsverlauf dieses Projekts sind aktuell zu "
            "umfangreich fuer eine Anfrage. Bitte nicht benoetigte Dokumente entfernen "
            "oder ein neues Projekt fuer das Thema anlegen."
        )

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        project_name=project_name, context=context or "(keine Dokumente zugeordnet)"
    )
    messages = [*history, {"role": "user", "content": question}]

    try:
        api_key = get_anthropic_api_key()
    except MissingAPIKeyError as exc:
        raise AIUnavailableError(str(exc)) from exc

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
        )
    except anthropic.AuthenticationError as exc:
        raise AIUnavailableError("Der Anthropic-API-Key ist ungueltig oder fehlt.") from exc
    except anthropic.RateLimitError as exc:
        raise AIUnavailableError("Das Anthropic-API-Kontingent ist erschoepft.") from exc
    except anthropic.APIConnectionError as exc:
        raise AIUnavailableError("Die Anthropic API ist aktuell nicht erreichbar.") from exc
    except anthropic.APIError as exc:
        raise AIUnavailableError(f"Anthropic API Fehler: {exc}") from exc

    answer_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    sources = []
    seen = set()
    for filename, page_number in SOURCE_PATTERN.findall(answer_text):
        filename = filename.strip()
        key = (filename, page_number)
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "document_id": filename_to_document_id.get(filename),
                "filename": filename,
                "page_number": int(page_number),
            }
        )

    return {"content": answer_text, "sources": sources}
