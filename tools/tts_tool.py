"""
Verifizer — tools/tts_tool.py
Text-to-speech wrapper using gTTS (Google Text-to-Speech).
Converts AI verdict / chat responses to audio bytes
that Streamlit can play directly with st.audio().

Only called when user interacts via VOICE input.
Text input → text output only (no TTS).
"""

import io
import re

from gtts import gTTS


# ── Supported languages ────────────────────────────────────────────────────────
# gTTS language codes — extend as needed
SUPPORTED_LANGUAGES = {
    "English":    "en",
    "Hindi":      "hi",
    "Odia":       "or",
    "Tamil":      "ta",
    "Telugu":     "te",
    "Bengali":    "bn",
    "Marathi":    "mr",
    "Kannada":    "kn",
    "Malayalam":  "ml",
    "Gujarati":   "gu",
    "Punjabi":    "pa",
}

DEFAULT_LANGUAGE = "en"


# ── Main function ──────────────────────────────────────────────────────────────

def text_to_speech(text: str, language: str = "English") -> dict:
    """
    Convert text to speech audio bytes.

    Args:
        text     : the text to speak
        language : language name from SUPPORTED_LANGUAGES keys
                   e.g. "English", "Hindi", "Tamil"

    Returns:
        {
            "success":     bool,
            "audio_bytes": bytes,   # MP3 bytes — pass to st.audio()
            "error":       str      # only on failure
        }
    """
    if not text or not text.strip():
        return {"success": False, "error": "No text provided for TTS."}

    lang_code = SUPPORTED_LANGUAGES.get(language, DEFAULT_LANGUAGE)

    try:
        cleaned = _clean_text_for_speech(text)

        # gTTS generates MP3 audio
        tts = gTTS(text=cleaned, lang=lang_code, slow=False)

        # Write to in-memory buffer — no disk writes needed
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)

        return {
            "success":     True,
            "audio_bytes": buffer.read(),
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"TTS error: {str(e)}",
        }


# ── Chunk TTS for long texts ───────────────────────────────────────────────────

def text_to_speech_chunked(text: str, language: str = "English") -> dict:
    """
    For long texts (verdicts, full explanations) — splits into chunks
    and concatenates audio bytes. gTTS has limits on very long strings.

    Args:
        text     : long text to speak
        language : language name

    Returns:
        Same structure as text_to_speech()
    """
    if not text or not text.strip():
        return {"success": False, "error": "No text provided."}

    lang_code = SUPPORTED_LANGUAGES.get(language, DEFAULT_LANGUAGE)
    cleaned   = _clean_text_for_speech(text)
    chunks    = _split_into_chunks(cleaned, max_chars=400)

    if not chunks:
        return {"success": False, "error": "Text could not be split into chunks."}

    try:
        combined_buffer = io.BytesIO()

        for chunk in chunks:
            if not chunk.strip():
                continue
            tts = gTTS(text=chunk, lang=lang_code, slow=False)
            chunk_buffer = io.BytesIO()
            tts.write_to_fp(chunk_buffer)
            chunk_buffer.seek(0)
            combined_buffer.write(chunk_buffer.read())

        combined_buffer.seek(0)

        return {
            "success":     True,
            "audio_bytes": combined_buffer.read(),
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Chunked TTS error: {str(e)}",
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean_text_for_speech(text: str) -> str:
    """
    Clean text before sending to TTS.
    Removes markdown, symbols, and formatting
    that would sound weird when spoken aloud.
    """
    # Remove markdown bold/italic
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)

    # Remove markdown headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove bullet points — replace with pause
    text = re.sub(r"^\s*[-•*]\s+", "", text, flags=re.MULTILINE)

    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove clause references like [Page 3], (Clause 4.2)
    text = re.sub(r"\[.*?\]|\(Clause.*?\)", "", text)

    # Remove emoji
    text = re.sub(r"[^\w\s\.,!?;:\-\'\"()]", " ", text)

    # Collapse multiple spaces / newlines
    text = re.sub(r"\n+", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def _split_into_chunks(text: str, max_chars: int = 400) -> list:
    """
    Split long text into chunks at sentence boundaries.
    Keeps chunks under max_chars to avoid gTTS limits.
    """
    # Split on sentence-ending punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks  = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current += (" " if current else "") + sentence
        else:
            if current:
                chunks.append(current.strip())
            # If single sentence is too long, split on commas
            if len(sentence) > max_chars:
                sub_parts = sentence.split(",")
                sub_chunk = ""
                for part in sub_parts:
                    if len(sub_chunk) + len(part) + 1 <= max_chars:
                        sub_chunk += ("," if sub_chunk else "") + part
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        sub_chunk = part
                if sub_chunk:
                    chunks.append(sub_chunk.strip())
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if c]


def get_supported_languages() -> list:
    """Returns list of supported language names for UI dropdown."""
    return list(SUPPORTED_LANGUAGES.keys())