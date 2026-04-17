"""
Verifizer — tools/tts_tool.py
Text-to-speech wrapper using gTTS.
Single call per response — no manual chunking.
gTTS handles splitting internally.
"""

import io
import re
from gtts import gTTS

SUPPORTED_LANGUAGES = {
    "English":   "en",
    "Hindi":     "hi",
    "Odia":      "or",
    "Tamil":     "ta",
    "Telugu":    "te",
    "Bengali":   "bn",
    "Marathi":   "mr",
    "Kannada":   "kn",
    "Malayalam": "ml",
    "Gujarati":  "gu",
    "Punjabi":   "pa",
}

DEFAULT_LANGUAGE = "en"


def text_to_speech(text: str, language: str = "English") -> dict:
    """
    Convert text to MP3 bytes via a single gTTS call.
    Returns raw bytes via .getvalue() — no seek needed.
    """
    if not text or not text.strip():
        return {"success": False, "error": "No text provided."}

    lang_code = SUPPORTED_LANGUAGES.get(language, DEFAULT_LANGUAGE)
    cleaned   = _clean_text_for_speech(text)

    if not cleaned.strip():
        return {"success": False, "error": "No speakable text after cleaning."}

    try:
        tts         = gTTS(text=cleaned, lang=lang_code, slow=False)
        buf         = io.BytesIO()
        tts.write_to_fp(buf)
        audio_bytes = buf.getvalue()   # getvalue() always returns full bytes

        if not audio_bytes:
            return {"success": False, "error": "gTTS returned empty audio."}

        return {"success": True, "audio_bytes": audio_bytes}

    except Exception as e:
        return {"success": False, "error": f"TTS error: {str(e)}"}


def text_to_speech_chunked(text: str, language: str = "English") -> dict:
    """
    Alias for text_to_speech — chunking removed.
    gTTS handles long text internally. Manual chunking corrupted MP3.
    """
    return text_to_speech(text, language)


def _clean_text_for_speech(text: str) -> str:
    """Strip markdown and formatting before TTS."""
    text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-•*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[.*?\]|\(Clause.*?\)", "", text)
    text = re.sub(r"[^\w\s\.,!?;:\-\'\"()]", " ", text)
    text = re.sub(r"\n+", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def get_supported_languages() -> list:
    return list(SUPPORTED_LANGUAGES.keys())