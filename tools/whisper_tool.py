"""
Verifizer — tools/whisper_tool.py
OpenAI Whisper API wrapper.
Transcribes uploaded audio files and live mic recordings.
Returns transcript text with timestamps where available.
"""

import io
import os
import tempfile
from pathlib import Path

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Model ──────────────────────────────────────────────────────────────────────
WHISPER_MODEL = "whisper-1"

# ── Max audio size Whisper accepts ────────────────────────────────────────────
MAX_WHISPER_SIZE_MB = 25


# ── Main function — uploaded file ─────────────────────────────────────────────

def transcribe_audio_file(audio_bytes: bytes, filename: str) -> dict:
    """
    Transcribe an uploaded audio file using Whisper.

    Args:
        audio_bytes : raw bytes of the audio file
        filename    : original filename (needed for extension / MIME type)

    Returns:
        {
            "success":     bool,
            "transcript":  str,          # full plain text transcript
            "segments":    list[dict],   # [{start, end, text}] for timestamps
            "language":    str,          # detected language
            "error":       str           # only on failure
        }
    """
    if not audio_bytes:
        return {"success": False, "error": "No audio data provided."}

    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_WHISPER_SIZE_MB:
        return {
            "success": False,
            "error":   f"Audio file too large ({size_mb:.1f} MB). Max {MAX_WHISPER_SIZE_MB} MB for transcription.",
        }

    extension = Path(filename).suffix.lower()
    if not extension:
        extension = ".mp3"

    try:
        # Whisper API needs a file-like object with a name attribute
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio{extension}"

        # ── Verbose JSON gives us segments with timestamps ─────────────────────
        response = client.audio.transcriptions.create(
            model           = WHISPER_MODEL,
            file            = audio_file,
            response_format = "verbose_json",   # gives segments + timestamps
            timestamp_granularities = ["segment"],
        )

        transcript = response.text.strip()
        segments   = _parse_segments(response)
        language   = getattr(response, "language", "unknown")

        return {
            "success":    True,
            "transcript": transcript,
            "segments":   segments,
            "language":   language,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Whisper API error: {str(e)}",
        }


# ── Live mic bytes ─────────────────────────────────────────────────────────────

def transcribe_mic_bytes(raw_bytes: bytes) -> dict:
    """
    Transcribe raw audio bytes captured from live mic (streamlit-webrtc).
    Saves to a temp WAV file first, then sends to Whisper.

    Args:
        raw_bytes : raw PCM or WebRTC audio bytes from mic

    Returns:
        Same structure as transcribe_audio_file()
    """
    if not raw_bytes or len(raw_bytes) < 1000:
        return {"success": False, "error": "Audio too short or empty."}

    try:
        # Write to temp file — Whisper needs a real file-like with extension
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model           = WHISPER_MODEL,
                file            = audio_file,
                response_format = "verbose_json",
                timestamp_granularities = ["segment"],
            )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

        transcript = response.text.strip()
        segments   = _parse_segments(response)
        language   = getattr(response, "language", "unknown")

        return {
            "success":    True,
            "transcript": transcript,
            "segments":   segments,
            "language":   language,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Mic transcription error: {str(e)}",
        }


# ── Segment parser ─────────────────────────────────────────────────────────────

def _parse_segments(response) -> list:
    """
    Parse Whisper verbose_json response into clean segment list.
    Each segment: { "start": "0:14", "end": "0:22", "text": "..." }

    Timestamps formatted as M:SS for human readability.
    """
    segments = []

    raw_segments = getattr(response, "segments", None)
    if not raw_segments:
        return segments

    for seg in raw_segments:
        start_sec = getattr(seg, "start", 0)
        end_sec   = getattr(seg, "end",   0)
        text      = getattr(seg, "text",  "").strip()

        if text:
            segments.append({
                "start": _format_timestamp(start_sec),
                "end":   _format_timestamp(end_sec),
                "text":  text,
            })

    return segments


def _format_timestamp(seconds: float) -> str:
    """
    Convert float seconds to human-readable M:SS format.
    e.g. 134.5 → "2:14"
    """
    seconds = int(seconds)
    mins    = seconds // 60
    secs    = seconds % 60
    return f"{mins}:{secs:02d}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_transcript_with_timestamps(segments: list) -> str:
    """
    Format segments into a readable transcript string with timestamps.
    Used when passing transcript to the claims agent.

    e.g.
    [0:00] Hello, this policy covers everything including hospitalization.
    [0:14] There is no waiting period for pre-existing conditions.
    """
    if not segments:
        return ""

    lines = []
    for seg in segments:
        lines.append(f"[{seg['start']}] {seg['text']}")

    return "\n".join(lines)


def get_plain_transcript(segments: list) -> str:
    """
    Return just the text from segments, no timestamps.
    Used when timestamps are not needed (e.g. typed claims comparison).
    """
    if not segments:
        return ""
    return " ".join(seg["text"] for seg in segments)