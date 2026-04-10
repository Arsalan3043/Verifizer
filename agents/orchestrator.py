"""
Verifizer — agents/orchestrator.py
Orchestrator Agent.
The master brain. Wires all agents together.

Two main flows:
  1. run_verification() — document + audio/typed claims → verdict
  2. run_document_parse() — document upload → structured extraction

The orchestrator decides:
  - Which agents to call
  - In what order
  - What data to pass between them
  - How to handle partial inputs (audio only, typed only, both)
"""

import streamlit as st

from agents.document_agent     import run_document_agent, build_document_context
from agents.audio_agent        import run_audio_agent
from agents.claims_agent       import run_claims_agent
from agents.verification_agent import run_verification_agent, load_skill_file
from utils.file_handler        import handle_audio_upload


# ── Flow 1 — Document parsing (called on upload) ───────────────────────────────

def run_document_parse(doc_text: str, image_b64: str, filename: str) -> dict:
    """
    Called by app.py when user uploads a document.
    Runs the document agent and returns structured extraction.

    Args:
        doc_text   : raw text extracted by PyMuPDF
        image_b64  : base64 image (for scanned PDFs / photos)
        filename   : original filename

    Returns:
        {
            "success":        bool,
            "extracted_text": str,
            "doc_type":       str,
            "used_vision":    bool,
            "error":          str
        }
    """
    result = run_document_agent(
        doc_text  = doc_text,
        image_b64 = image_b64,
        filename  = filename,
    )

    return result


# ── Flow 2 — Verification (called on verify button) ────────────────────────────

def run_verification(
    doc_text:     str,
    skill:        str = "Auto-detect",
    audio_file    = None,
    typed_claims: str = None,
) -> dict:
    """
    Main verification flow. Called by app.py when user clicks 'Run Verification'.

    Orchestrates:
        1. Audio agent       — if audio file provided
        2. Claims agent      — extracts claims from audio + typed input
        3. Skill loader      — loads relevant domain knowledge
        4. Verification agent — cross-checks claims vs document

    Args:
        doc_text     : extracted document text from session state
        skill        : selected document type from UI dropdown
        audio_file   : Streamlit UploadedFile object (optional)
        typed_claims : raw string from text area (optional)

    Returns:
        Verification result dict from verification_agent, or error dict.
    """

    # ── Guard: need at least one claim source ──────────────────────────────────
    has_audio  = audio_file is not None
    has_typed  = bool(typed_claims and typed_claims.strip())

    if not has_audio and not has_typed:
        return _error("Please upload a recording or type what you were told.")

    if not doc_text or not doc_text.strip():
        return _error("No document loaded. Please upload a document first.")

    # ── Step 1: Transcribe audio (if provided) ─────────────────────────────────
    transcript             = None
    transcript_timestamped = None

    if has_audio:
        with st.spinner("Transcribing audio..."):
            audio_result = _handle_audio(audio_file)

        if not audio_result["success"]:
            return _error(f"Audio transcription failed: {audio_result['error']}")

        transcript             = audio_result["transcript"]
        transcript_timestamped = audio_result["transcript_timestamped"]

    # ── Step 2: Extract claims ─────────────────────────────────────────────────
    with st.spinner("Extracting claims..."):
        claims_result = run_claims_agent(
            transcript             = transcript,
            transcript_timestamped = transcript_timestamped,
            typed_claims           = typed_claims,
        )

    if not claims_result["success"]:
        return _error(f"Claims extraction failed: {claims_result['error']}")

    claims = claims_result["claims"]

    if not claims:
        return _error(
            "No specific verifiable claims were found in the input. "
            "Try adding more detail about what you were told."
        )

    # ── Step 3: Load skill file ────────────────────────────────────────────────
    # Use user-selected skill if provided, else fall back to auto-detected type
    skill_text = load_skill_file(skill)

    # ── Step 4: Build document context ────────────────────────────────────────
    # doc_text here is already the structured extraction from document_agent
    # (stored in session state after upload)
    document_context = build_document_context(
        extracted_text = doc_text,
        doc_type       = skill,
        skill_text     = skill_text,
    )

    # ── Step 5: Run verification ───────────────────────────────────────────────
    with st.spinner("Verifying claims against document..."):
        verification_result = run_verification_agent(
            document_context = document_context,
            claims           = claims,
            skill_text       = skill_text,
        )

    if not verification_result["success"]:
        return _error(f"Verification failed: {verification_result['error']}")

    # ── Return final result ────────────────────────────────────────────────────
    return verification_result


# ── Audio handler ──────────────────────────────────────────────────────────────

def _handle_audio(audio_file) -> dict:
    """
    Reads and validates the uploaded audio file,
    then passes to audio agent for transcription.

    Args:
        audio_file : Streamlit UploadedFile object

    Returns:
        Audio agent result dict
    """
    # Validate via file_handler first
    success, result = handle_audio_upload(audio_file)

    if not success:
        return {"success": False, "error": result}

    # Run audio agent
    audio_result = run_audio_agent(
        audio_bytes = result["bytes"],
        filename    = result["filename"],
    )

    return audio_result


# ── Error helper ───────────────────────────────────────────────────────────────

def _error(message: str) -> dict:
    """
    Returns a standardized error dict that app.py
    knows how to display cleanly.
    """
    return {
        "success":       False,
        "error":         message,
        "claims":        [],
        "honest_count":  0,
        "mislead_count": 0,
        "false_count":   0,
        "total":         0,
        "summary_note":  "",
    }