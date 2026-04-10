"""
Verifizer — agents/claims_agent.py
Claims Agent.
Takes a transcript (from audio) or typed text (from user)
and extracts every specific promise, claim, or assurance
made by the other party — with timestamps where available.

Output is a structured list of claims passed to
verification_agent for cross-checking against the document.
"""

import os
import json
import re

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Model ──────────────────────────────────────────────────────────────────────
CLAIMS_MODEL = "gpt-4o-mini"   # Cheaper model — extraction task, not reasoning


# ── System prompt ──────────────────────────────────────────────────────────────
CLAIMS_EXTRACTION_PROMPT = """
You are an expert at identifying specific promises, claims, and assurances 
made by salespeople, agents, HR professionals, landlords, or any party 
trying to convince someone to sign a document or agree to terms.

Your job is to read a transcript or typed summary and extract EVERY specific 
claim that was made — especially ones that could be verified against a document.

For each claim extract:
1. The exact claim or promise made (in plain language)
2. The timestamp if available (from transcript format [M:SS])
3. Who made the claim if identifiable (e.g. "agent", "HR", "landlord")
4. How specific or verifiable it is (high/medium/low)

Focus on claims like:
- Coverage promises ("this covers everything", "no waiting period")
- Financial promises ("no hidden charges", "EMI will be X amount")
- Process promises ("claim will be settled in 3 days")
- Exclusion denials ("pre-existing conditions are covered")
- Benefit claims ("you get free add-ons", "maternity is included")
- Obligation minimizations ("notice period is just 2 weeks")
- Exit/cancellation promises ("you can cancel anytime")

IGNORE:
- General pleasantries and small talk
- Vague statements that cannot be verified ("you'll love this policy")
- Questions asked by the customer
- Statements about the company's general reputation

OUTPUT FORMAT — return ONLY valid JSON, no explanation, no markdown:
{
  "claims": [
    {
      "claim": "exact claim text here",
      "timestamp": "2:14",
      "speaker": "agent",
      "specificity": "high"
    }
  ],
  "total_claims": 3,
  "source_type": "audio_transcript"
}

If no verifiable claims are found, return:
{
  "claims": [],
  "total_claims": 0,
  "source_type": "audio_transcript"
}
""".strip()


# ── Main function ──────────────────────────────────────────────────────────────

def run_claims_agent(
    transcript: str = None,
    transcript_timestamped: str = None,
    typed_claims: str = None,
) -> dict:
    """
    Entry point called by orchestrator.
    Accepts audio transcript OR typed claims OR both.

    Args:
        transcript             : plain text transcript from audio agent
        transcript_timestamped : timestamped transcript [M:SS] from audio agent
        typed_claims           : raw text typed by user in the UI

    Returns:
        {
            "success":     bool,
            "claims":      list[dict],   # [{claim, timestamp, speaker, specificity}]
            "total":       int,
            "source":      str,          # "audio" | "typed" | "both"
            "error":       str           # only on failure
        }
    """
    # ── Determine what input we have ───────────────────────────────────────────
    has_audio  = bool(transcript and transcript.strip())
    has_typed  = bool(typed_claims and typed_claims.strip())

    if not has_audio and not has_typed:
        return {
            "success": False,
            "error":   "Claims agent received no input. Provide transcript or typed claims.",
        }

    # ── Build user message ─────────────────────────────────────────────────────
    user_message = _build_user_message(
        transcript             = transcript,
        transcript_timestamped = transcript_timestamped,
        typed_claims           = typed_claims,
        has_audio              = has_audio,
        has_typed              = has_typed,
    )

    # ── Call GPT-4o-mini ───────────────────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model       = CLAIMS_MODEL,
            messages    = [
                {"role": "system", "content": CLAIMS_EXTRACTION_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens  = 1500,
            temperature = 0.1,
            response_format = {"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        parsed = _parse_response(raw)

        if parsed is None:
            return {
                "success": False,
                "error":   "Claims agent returned invalid JSON.",
            }

        claims = parsed.get("claims", [])
        claims = _validate_claims(claims)

        # ── Determine source ───────────────────────────────────────────────────
        if has_audio and has_typed:
            source = "both"
        elif has_audio:
            source = "audio"
        else:
            source = "typed"

        return {
            "success": True,
            "claims":  claims,
            "total":   len(claims),
            "source":  source,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Claims agent error: {str(e)}",
        }


# ── Message builder ────────────────────────────────────────────────────────────

def _build_user_message(
    transcript: str,
    transcript_timestamped: str,
    typed_claims: str,
    has_audio: bool,
    has_typed: bool,
) -> str:
    """
    Builds the user message sent to GPT-4o-mini.
    Prefers timestamped transcript for better claim attribution.
    """
    parts = []

    if has_audio:
        # Use timestamped version if available, fallback to plain
        audio_text = transcript_timestamped if transcript_timestamped else transcript
        parts.append(
            "AUDIO TRANSCRIPT (with timestamps):\n"
            "The following is a transcription of a recorded call or voice note.\n"
            "Extract all claims made by the agent/seller/HR/landlord.\n\n"
            f"{audio_text}"
        )

    if has_typed:
        parts.append(
            "TYPED SUMMARY (what the user was told):\n"
            "The following is what the user typed from memory or notes.\n"
            "Treat each point as a separate claim.\n\n"
            f"{typed_claims}"
        )

    if has_audio and has_typed:
        parts.append(
            "NOTE: Both audio transcript and typed summary are provided. "
            "Extract claims from both sources. Avoid duplicating the same claim twice."
        )

    parts.append(
        "\nExtract ALL verifiable claims and return as JSON."
    )

    return "\n\n".join(parts)


# ── Response parser ────────────────────────────────────────────────────────────

def _parse_response(raw: str) -> dict | None:
    """
    Safely parse JSON response from GPT-4o-mini.
    Handles cases where model wraps JSON in markdown fences.
    """
    try:
        # Strip markdown fences if present
        cleaned = re.sub(r"```json|```", "", raw).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ── Claims validator ───────────────────────────────────────────────────────────

def _validate_claims(claims: list) -> list:
    """
    Ensures each claim dict has all required fields.
    Fills in defaults for missing optional fields.
    """
    validated = []

    for item in claims:
        if not isinstance(item, dict):
            continue

        claim_text = item.get("claim", "").strip()
        if not claim_text:
            continue       # Skip empty claims

        validated.append({
            "claim":       claim_text,
            "timestamp":   item.get("timestamp", ""),      # Empty string if no timestamp
            "speaker":     item.get("speaker", "unknown"),
            "specificity": item.get("specificity", "medium"),
        })

    return validated


# ── Helpers ────────────────────────────────────────────────────────────────────

def format_claims_for_prompt(claims: list) -> str:
    """
    Formats extracted claims into a numbered list string
    for passing to the verification agent prompt.

    e.g.
    1. [2:14] "Covers all hospitalization" (speaker: agent)
    2. [3:40] "No waiting period for pre-existing conditions" (speaker: agent)
    3. [typed] "EMI will remain fixed for entire tenure"
    """
    if not claims:
        return "No specific claims found."

    lines = []
    for i, c in enumerate(claims, 1):
        timestamp = f"[{c['timestamp']}] " if c.get("timestamp") else "[typed] "
        speaker   = f"(speaker: {c['speaker']})" if c.get("speaker") != "unknown" else ""
        lines.append(f"{i}. {timestamp}\"{c['claim']}\" {speaker}".strip())

    return "\n".join(lines)