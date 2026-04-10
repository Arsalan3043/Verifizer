"""
Verifizer — agents/audio_agent.py
Audio Agent.
Receives uploaded audio bytes or live mic bytes,
calls whisper_tool to transcribe,
and returns a clean transcript with timestamps
ready for the claims agent to process.
"""

from tools.whisper_tool import (
    transcribe_audio_file,
    transcribe_mic_bytes,
    get_transcript_with_timestamps,
    get_plain_transcript,
)


# ── Main function — uploaded file ──────────────────────────────────────────────

def run_audio_agent(audio_bytes: bytes, filename: str) -> dict:
    """
    Entry point called by orchestrator for uploaded audio recordings.

    Args:
        audio_bytes : raw bytes of the uploaded audio file
        filename    : original filename (for extension detection)

    Returns:
        {
            "success":              bool,
            "transcript":           str,    # plain text, no timestamps
            "transcript_timestamped": str,  # [M:SS] text format
            "segments":             list,   # raw segment dicts [{start, end, text}]
            "language":             str,    # detected language
            "error":                str     # only on failure
        }
    """
    if not audio_bytes:
        return {"success": False, "error": "No audio data provided to audio agent."}

    # ── Transcribe ─────────────────────────────────────────────────────────────
    result = transcribe_audio_file(audio_bytes=audio_bytes, filename=filename)

    if not result["success"]:
        return {
            "success": False,
            "error":   result.get("error", "Transcription failed."),
        }

    segments = result.get("segments", [])

    # ── Build both transcript formats ──────────────────────────────────────────
    transcript_plain       = result.get("transcript", "") or get_plain_transcript(segments)
    transcript_timestamped = get_transcript_with_timestamps(segments)

    # ── Validate output ────────────────────────────────────────────────────────
    if not transcript_plain.strip():
        return {
            "success": False,
            "error":   "Transcription returned empty text. Audio may be silent or too noisy.",
        }

    return {
        "success":                True,
        "transcript":             transcript_plain,
        "transcript_timestamped": transcript_timestamped,
        "segments":               segments,
        "language":               result.get("language", "unknown"),
    }


# ── Live mic entry point ───────────────────────────────────────────────────────

def run_mic_agent(raw_bytes: bytes) -> dict:
    """
    Entry point for live mic audio captured via streamlit-webrtc.
    Used in interactive voice Q&A mode (V2).

    Args:
        raw_bytes : raw PCM/WAV bytes from mic capture

    Returns:
        Same structure as run_audio_agent()
    """
    if not raw_bytes or len(raw_bytes) < 1000:
        return {
            "success": False,
            "error":   "Mic audio too short or empty. Please speak clearly and try again.",
        }

    result = transcribe_mic_bytes(raw_bytes=raw_bytes)

    if not result["success"]:
        return {
            "success": False,
            "error":   result.get("error", "Mic transcription failed."),
        }

    segments               = result.get("segments", [])
    transcript_plain       = result.get("transcript", "") or get_plain_transcript(segments)
    transcript_timestamped = get_transcript_with_timestamps(segments)

    if not transcript_plain.strip():
        return {
            "success": False,
            "error":   "Could not transcribe mic input. Please speak louder or check mic permissions.",
        }

    return {
        "success":                True,
        "transcript":             transcript_plain,
        "transcript_timestamped": transcript_timestamped,
        "segments":               segments,
        "language":               result.get("language", "unknown"),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_audio_summary(transcript: str, segments: list) -> str:
    """
    Returns a brief summary of the audio for display in the UI.
    Shows duration, word count, and detected language.

    Args:
        transcript : plain text transcript
        segments   : list of segment dicts

    Returns:
        Human-readable summary string.
    """
    word_count = len(transcript.split()) if transcript else 0

    duration = ""
    if segments:
        last_seg  = segments[-1]
        duration  = f" · Duration ~{last_seg['end']}"

    return f"{word_count} words transcribed{duration}"


def format_transcript_for_display(segments: list, max_segments: int = 20) -> str:
    """
    Formats a transcript for display in the Streamlit UI.
    Shows timestamped lines, capped at max_segments for readability.

    Args:
        segments     : list of segment dicts
        max_segments : max lines to show before truncating

    Returns:
        Formatted string for st.text() or st.markdown()
    """
    if not segments:
        return "No transcript available."

    lines = []
    for seg in segments[:max_segments]:
        lines.append(f"`[{seg['start']}]` {seg['text']}")

    result = "\n\n".join(lines)

    if len(segments) > max_segments:
        remaining = len(segments) - max_segments
        result += f"\n\n_... and {remaining} more segments_"

    return result