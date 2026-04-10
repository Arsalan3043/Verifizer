"""
Verifizer — agents/document_agent.py
Document Agent.
Receives raw file content (text + optional image),
calls vision_tool to extract structured information,
and returns a clean document context ready for
verification and chat agents to use.
"""

from tools.vision_tool import extract_document, _detect_doc_type
from utils.file_handler import is_scanned_pdf, truncate_text


# ── Main agent function ────────────────────────────────────────────────────────

def run_document_agent(doc_text: str = None, image_b64: str = None, filename: str = "") -> dict:
    """
    Entry point called by orchestrator when a document is uploaded.

    Decides whether to use text extraction, Vision, or both —
    then returns a structured document context.

    Args:
        doc_text   : plain text extracted by PyMuPDF (may be empty for scanned PDFs)
        image_b64  : base64 image (for scanned PDFs or photo uploads)
        filename   : original filename (for logging/display)

    Returns:
        {
            "success":          bool,
            "extracted_text":   str,    # structured extraction from GPT-4o
            "raw_text":         str,    # original PyMuPDF text (for reference)
            "doc_type":         str,    # detected document type
            "used_vision":      bool,   # whether Vision API was used
            "error":            str     # only on failure
        }
    """

    if not doc_text and not image_b64:
        return {
            "success": False,
            "error":   "Document agent received no content. Pass doc_text or image_b64.",
        }

    # ── Decide extraction strategy ─────────────────────────────────────────────
    has_good_text = doc_text and not is_scanned_pdf(doc_text)
    needs_vision  = image_b64 is not None or is_scanned_pdf(doc_text or "")
    used_vision   = needs_vision

    strategy = _decide_strategy(has_good_text, needs_vision)

    # ── Run extraction ─────────────────────────────────────────────────────────
    if strategy == "text_only":
        result = extract_document(doc_text=doc_text, image_b64=None)

    elif strategy == "vision_only":
        result = extract_document(doc_text=None, image_b64=image_b64)

    elif strategy == "both":
        result = extract_document(doc_text=doc_text, image_b64=image_b64)

    else:
        return {"success": False, "error": "Unknown extraction strategy."}

    # ── Handle extraction failure ──────────────────────────────────────────────
    if not result["success"]:
        return {
            "success": False,
            "error":   result.get("error", "Document extraction failed."),
        }

    extracted_text = result["extracted_text"]
    doc_type       = result.get("doc_type") or _detect_doc_type(extracted_text)

    # ── Post-process ───────────────────────────────────────────────────────────
    extracted_text = _post_process(extracted_text)

    return {
        "success":        True,
        "extracted_text": extracted_text,
        "raw_text":       doc_text or "",
        "doc_type":       doc_type,
        "used_vision":    used_vision,
    }


# ── Strategy selector ──────────────────────────────────────────────────────────

def _decide_strategy(has_good_text: bool, needs_vision: bool) -> str:
    """
    Decides which extraction path to use.

    Logic:
    - Good text + no image needed  → text_only  (cheaper)
    - No good text + image exists  → vision_only
    - Good text + image also exists → both       (best accuracy)
    """
    if has_good_text and not needs_vision:
        return "text_only"
    elif not has_good_text and needs_vision:
        return "vision_only"
    elif has_good_text and needs_vision:
        return "both"
    else:
        # Fallback: try vision if image available, else text
        return "vision_only" if needs_vision else "text_only"


# ── Post-processor ─────────────────────────────────────────────────────────────

def _post_process(extracted_text: str) -> str:
    """
    Light cleanup of extracted text before storing in session.
    - Strips excessive blank lines
    - Ensures text is not empty
    """
    if not extracted_text:
        return ""

    # Collapse 3+ blank lines into 2
    import re
    extracted_text = re.sub(r"\n{3,}", "\n\n", extracted_text)

    return extracted_text.strip()


# ── Context builder ────────────────────────────────────────────────────────────

def build_document_context(extracted_text: str, doc_type: str, skill_text: str = "") -> str:
    """
    Assembles the full document context string passed to
    verification_agent and chat_agent as their knowledge base.

    Combines:
        - Structured extraction from document
        - Skill file content (red flags, rights, known traps)

    Args:
        extracted_text : output from run_document_agent()
        doc_type       : detected or user-selected document type
        skill_text     : contents of the relevant skill .md file (optional)

    Returns:
        Single string used as context in all downstream agent prompts.
    """
    parts = []

    parts.append(f"DOCUMENT TYPE: {doc_type}")
    parts.append("=" * 50)
    parts.append("DOCUMENT CONTENT (EXTRACTED):")
    parts.append(extracted_text)

    if skill_text and skill_text.strip():
        parts.append("=" * 50)
        parts.append("DOMAIN KNOWLEDGE & RED FLAGS FOR THIS DOCUMENT TYPE:")
        parts.append(skill_text)

    return "\n\n".join(parts)