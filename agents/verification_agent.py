"""
Verifizer — agents/verification_agent.py
Verification Agent.
The core intelligence of Verifizer.

Takes:
  - Structured document context (from document_agent)
  - Extracted claims list (from claims_agent)
  - Relevant skill file content (loaded by orchestrator)

Produces:
  - A verdict for EACH claim: Honest / Misleading / False
  - Clause reference from the document
  - Timestamp from audio (if available)
  - Explanation in plain language
  - An overall summary note
"""

import os
import json
import re

from openai import OpenAI
from agents.claims_agent import format_claims_for_prompt

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Models ─────────────────────────────────────────────────────────────────────
VERIFICATION_MODEL = "gpt-4o"       # Full GPT-4o — this is the reasoning step
                                     # Quality matters here, don't use mini


# ── System prompt ──────────────────────────────────────────────────────────────
VERIFICATION_SYSTEM_PROMPT = """
You are a document verification expert and consumer rights advisor.

You will be given:
1. A structured extraction of a document (insurance policy, rent agreement, offer letter, loan agreement, etc.)
2. A list of claims made verbally or in writing by an agent, salesperson, HR, or landlord
3. Domain knowledge about common red flags for this document type (if provided)

Your job is to cross-check EVERY claim against the document and give a verdict.

VERDICT OPTIONS:
- "honest"   : The document supports or is consistent with the claim
- "mislead"  : The claim is technically not false but omits important conditions,
               limits, or exceptions that significantly change the meaning
- "false"    : The document directly contradicts the claim

RULES:
- Be precise. Quote the specific clause, section, or page that supports your verdict.
- If the document is silent on a claim (doesn't mention it at all), verdict is "mislead"
  because omission of important terms is itself misleading.
- Use plain language in explanations. Write as if explaining to someone with no legal background.
- Be strict. Salespeople often use technically true statements that are deeply misleading.
  Treat those as "mislead" not "honest".
- Do NOT add generic advice. Only verify claims against the document provided.

OUTPUT FORMAT — return ONLY valid JSON, no explanation, no markdown:
{
  "claims": [
    {
      "claim": "exact claim text",
      "verdict": "honest" | "mislead" | "false",
      "explanation": "plain language explanation of why",
      "clause_ref": "Section 4.2 / Page 3 / Exclusions Clause",
      "timestamp": "2:14"
    }
  ],
  "honest_count": 2,
  "mislead_count": 1,
  "false_count": 1,
  "total": 4,
  "summary_note": "2 out of 4 claims have issues. Most concerning: the agent claimed no waiting period but the document shows a 2-year waiting period for pre-existing conditions."
}
""".strip()


# ── Main function ──────────────────────────────────────────────────────────────

def run_verification_agent(
    document_context: str,
    claims: list,
    skill_text: str = "",
) -> dict:
    """
    Entry point called by orchestrator.
    Cross-checks all extracted claims against the document.

    Args:
        document_context : full extracted document text + skill file (from document_agent)
        claims           : list of claim dicts from claims_agent
        skill_text       : contents of relevant skill .md file (optional, may already
                           be embedded in document_context)

    Returns:
        {
            "success":       bool,
            "claims":        list[dict],  # verdict for each claim
            "honest_count":  int,
            "mislead_count": int,
            "false_count":   int,
            "total":         int,
            "summary_note":  str,
            "error":         str          # only on failure
        }
    """
    if not document_context or not document_context.strip():
        return {"success": False, "error": "No document context provided to verification agent."}

    if not claims:
        return {"success": False, "error": "No claims provided to verification agent."}

    try:
        user_message = _build_verification_message(
            document_context = document_context,
            claims           = claims,
            skill_text       = skill_text,
        )

        response = client.chat.completions.create(
            model           = VERIFICATION_MODEL,
            messages        = [
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens      = 3000,
            temperature     = 0.1,
            response_format = {"type": "json_object"},
        )

        raw    = response.choices[0].message.content.strip()
        parsed = _parse_response(raw)

        if parsed is None:
            return {"success": False, "error": "Verification agent returned invalid JSON."}

        # ── Validate and enrich output ─────────────────────────────────────────
        verified_claims = _validate_and_enrich(parsed.get("claims", []), claims)
        counts          = _count_verdicts(verified_claims)

        return {
            "success":       True,
            "claims":        verified_claims,
            "honest_count":  counts["honest"],
            "mislead_count": counts["mislead"],
            "false_count":   counts["false"],
            "total":         len(verified_claims),
            "summary_note":  parsed.get("summary_note", ""),
        }

    except Exception as e:
        return {"success": False, "error": f"Verification agent error: {str(e)}"}


# ── Message builder ────────────────────────────────────────────────────────────

def _build_verification_message(
    document_context: str,
    claims: list,
    skill_text: str = "",
) -> str:
    """
    Assembles the full user message for the verification prompt.
    Structured clearly so GPT-4o can reason claim-by-claim.
    """
    formatted_claims = format_claims_for_prompt(claims)

    parts = []

    # ── Document section ───────────────────────────────────────────────────────
    parts.append(
        "DOCUMENT TO VERIFY AGAINST:\n"
        "═" * 50 + "\n"
        f"{document_context}"
    )

    # ── Skill / domain knowledge ───────────────────────────────────────────────
    if skill_text and skill_text.strip():
        parts.append(
            "DOMAIN KNOWLEDGE & RED FLAGS:\n"
            "═" * 50 + "\n"
            f"{skill_text}"
        )

    # ── Claims to verify ───────────────────────────────────────────────────────
    parts.append(
        "CLAIMS TO VERIFY:\n"
        "═" * 50 + "\n"
        "The following claims were made verbally or in writing.\n"
        "Verify each one against the document above.\n\n"
        f"{formatted_claims}"
    )

    parts.append(
        "Verify each claim carefully against the document. "
        "Return verdicts for ALL claims in the specified JSON format."
    )

    return "\n\n".join(parts)


# ── Response parser ────────────────────────────────────────────────────────────

def _parse_response(raw: str) -> dict | None:
    """Safely parse JSON from GPT-4o response."""
    try:
        cleaned = re.sub(r"```json|```", "", raw).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


# ── Output validator ───────────────────────────────────────────────────────────

def _validate_and_enrich(verified_claims: list, original_claims: list) -> list:
    """
    Validates each verified claim dict has all required fields.
    Re-attaches timestamps from original claims if missing in response.
    Normalizes verdict values.
    """
    # Build timestamp lookup from original claims
    timestamp_map = {}
    for c in original_claims:
        key = c.get("claim", "").strip().lower()
        if key and c.get("timestamp"):
            timestamp_map[key] = c["timestamp"]

    validated = []
    valid_verdicts = {"honest", "mislead", "false"}

    for item in verified_claims:
        if not isinstance(item, dict):
            continue

        claim_text = item.get("claim", "").strip()
        if not claim_text:
            continue

        # Normalize verdict
        verdict = item.get("verdict", "").lower().strip()
        if verdict not in valid_verdicts:
            verdict = "mislead"   # Default to misleading if uncertain

        # Re-attach timestamp from original claims if missing
        timestamp = item.get("timestamp", "")
        if not timestamp:
            timestamp = timestamp_map.get(claim_text.lower(), "")

        validated.append({
            "claim":       claim_text,
            "verdict":     verdict,
            "explanation": item.get("explanation", "No explanation provided.").strip(),
            "clause_ref":  item.get("clause_ref", "").strip(),
            "timestamp":   timestamp,
        })

    return validated


# ── Verdict counter ────────────────────────────────────────────────────────────

def _count_verdicts(claims: list) -> dict:
    """Count how many claims fall into each verdict category."""
    counts = {"honest": 0, "mislead": 0, "false": 0}
    for c in claims:
        verdict = c.get("verdict", "").lower()
        if verdict in counts:
            counts[verdict] += 1
    return counts


# ── Skill loader ───────────────────────────────────────────────────────────────

def load_skill_file(doc_type: str) -> str:
    """
    Loads the relevant skill .md file based on document type.
    Returns empty string if no matching skill file exists.

    Skill files live in the /skills/ directory.
    Each file contains red flags, known misleading phrases,
    and consumer rights for that document category.

    Args:
        doc_type : document type string e.g. "Health Insurance", "Rent Agreement"

    Returns:
        Contents of skill file as string, or empty string.
    """
    import os
    from pathlib import Path

    # Map doc_type to skill filename
    skill_map = {
        "Health Insurance": "health_insurance.md",
        "Rent Agreement":   "rent_agreement.md",
        "Employment Offer": "employment_offer.md",
        "Loan Agreement":   "loan_agreement.md",
        "General":          "",                    # No skill file for general
        "Auto-detect":      "",
        "Warranty":         "",
    }

    filename = skill_map.get(doc_type, "")
    if not filename:
        return ""

    skill_path = Path(__file__).parent.parent / "skills" / filename

    if not skill_path.exists():
        return ""

    try:
        return skill_path.read_text(encoding="utf-8")
    except Exception:
        return ""