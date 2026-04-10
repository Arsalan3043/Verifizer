"""
Verifizer — utils/session_state.py
Initializes and manages all Streamlit session state variables.
Call init_session_state() once at the top of app.py.
"""

import streamlit as st


def init_session_state():
    """
    Set default values for all session state keys.
    Only sets a key if it doesn't already exist —
    so existing values are never overwritten on rerun.
    """

    defaults = {

        # ── Document ──────────────────────────────────────────
        "doc_parsed":   False,   # True once document is read successfully
        "doc_text":     None,    # Extracted plain text from the document
        "doc_filename": None,    # Original filename (shown in status bar)
        "doc_type":     None,    # "pdf" or "image"

        # ── Skill / document category ─────────────────────────
        "skill_choice": "Auto-detect",  # Selected from dropdown

        # ── Verify tab ────────────────────────────────────────
        "audio_transcript":     None,   # Whisper transcript of uploaded audio
        "extracted_claims":     None,   # List of claims pulled from transcript/text
        "verification_result":  None,   # Final verdict dict from verification agent

        # ── Chat tab ──────────────────────────────────────────
        # Each entry: {"role": "user"|"assistant", "content": str, "audio_bytes": bytes|None}
        "chat_history": [],

    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_document_state():
    """
    Call this when a new document is uploaded.
    Clears all derived data so stale results don't carry over.
    """
    st.session_state.doc_parsed          = False
    st.session_state.doc_text            = None
    st.session_state.doc_filename        = None
    st.session_state.doc_type            = None
    st.session_state.skill_choice        = "Auto-detect"
    st.session_state.audio_transcript    = None
    st.session_state.extracted_claims    = None
    st.session_state.verification_result = None
    st.session_state.chat_history        = []


def reset_verification_state():
    """
    Call this when the user uploads a new audio file or changes typed claims.
    Only clears verification output, keeps document and chat intact.
    """
    st.session_state.audio_transcript    = None
    st.session_state.extracted_claims    = None
    st.session_state.verification_result = None