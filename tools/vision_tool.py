"""
Verifizer — tools/vision_tool.py
GPT-4o Vision wrapper.
Sends document (text or image) to GPT-4o and extracts
all clauses, terms, conditions, and key information
in a structured plain-text format.
"""

import os
from openai import OpenAI
from utils.file_handler import truncate_text

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Model ──────────────────────────────────────────────────────────────────────
VISION_MODEL = "gpt-4o"   # Vision only works on gpt-4o, not mini


# ── System prompt ──────────────────────────────────────────────────────────────
DOCUMENT_EXTRACTION_PROMPT = """
You are a document analysis expert. Your job is to read any document — insurance policy, 
rent agreement, employment offer, loan agreement, warranty card, or any contract — and 
extract ALL important information in a clear, structured format.

Extract and organize the following:

1. DOCUMENT TYPE — What kind of document is this?
2. KEY TERMS & CONDITIONS — All important clauses, rules, and obligations
3. WHAT IS COVERED / INCLUDED — Benefits, inclusions, entitlements
4. WHAT IS NOT COVERED / EXCLUDED — Exclusions, exceptions, limitations
5. IMPORTANT NUMBERS — Amounts, percentages, dates, durations, limits
6. HIDDEN OR TRICKY CLAUSES — Fine print, conditions that could disadvantage the user
7. OBLIGATIONS ON THE USER — What the user must do, deadlines, penalties
8. CANCELLATION / EXIT TERMS — How to exit, penalties, notice periods

Rules:
- Be thorough. Do not summarize away important details.
- Use plain language. Avoid legal jargon.
- If something is ambiguous or vague in the document, flag it explicitly.
- Preserve clause numbers or section references where visible (e.g. "Clause 4.2").
- Output in clean plain text with clear section headers.
- Do NOT add opinions or advice — only extract what the document says.
""".strip()


# ── Main function ──────────────────────────────────────────────────────────────

def extract_document(doc_text: str = None, image_b64: str = None) -> dict:
    """
    Extract structured information from a document.

    Pass either:
        doc_text   — for text-based PDFs (already extracted by PyMuPDF)
        image_b64  — for scanned PDFs or uploaded images

    You can pass both — text + image — for best results on hybrid docs.

    Returns:
        {
            "success":        bool,
            "extracted_text": str,    # structured extraction result
            "doc_type":       str,    # detected document type
            "error":          str     # only present on failure
        }
    """
    if not doc_text and not image_b64:
        return {
            "success": False,
            "error":   "No document content provided. Pass doc_text or image_b64.",
        }

    try:
        messages = _build_messages(doc_text, image_b64)

        response = client.chat.completions.create(
            model      = VISION_MODEL,
            messages   = messages,
            max_tokens = 2000,
            temperature= 0.1,    # Low temp — we want factual extraction, not creativity
        )

        extracted = response.choices[0].message.content.strip()
        doc_type  = _detect_doc_type(extracted)

        return {
            "success":        True,
            "extracted_text": extracted,
            "doc_type":       doc_type,
        }

    except Exception as e:
        return {
            "success": False,
            "error":   f"Vision API error: {str(e)}",
        }


# ── Message builder ────────────────────────────────────────────────────────────

def _build_messages(doc_text: str = None, image_b64: str = None) -> list:
    """
    Builds the messages array for the GPT-4o API call.
    Handles three cases:
        1. Text only  — PDF with good text extraction
        2. Image only — scanned PDF or photo
        3. Both       — hybrid: use text + image together
    """
    user_content = []

    # ── Case 1 / 3: Text available ────────────────────────────────────────────
    if doc_text and doc_text.strip():
        truncated = truncate_text(doc_text, max_chars=12000)
        user_content.append({
            "type": "text",
            "text": f"Here is the document text:\n\n{truncated}\n\nPlease extract and structure all important information."
        })

    # ── Case 2 / 3: Image available ───────────────────────────────────────────
    if image_b64:
        user_content.append({
            "type": "text",
            "text": "Here is the document image. Please read it carefully and extract all visible text and information:"
        })
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url":    f"data:image/jpeg;base64,{image_b64}",
                "detail": "high",    # high detail = more tokens but better OCR accuracy
            }
        })
        user_content.append({
            "type": "text",
            "text": "Extract and structure all important information from this document."
        })

    # ── Fallback: nothing usable ───────────────────────────────────────────────
    if not user_content:
        user_content.append({
            "type": "text",
            "text": "No document content was provided."
        })

    return [
        {"role": "system",  "content": DOCUMENT_EXTRACTION_PROMPT},
        {"role": "user",    "content": user_content},
    ]


# ── Doc type detector ──────────────────────────────────────────────────────────

def _detect_doc_type(extracted_text: str) -> str:
    """
    Lightweight heuristic to detect document category
    from the extracted text. Used to auto-select skill file.
    """
    text_lower = extracted_text.lower()

    if any(kw in text_lower for kw in ["premium", "insured", "policyholder", "hospitalization", "coverage", "irdai"]):
        return "Health Insurance"

    if any(kw in text_lower for kw in ["tenant", "landlord", "rent", "lease", "premises", "security deposit"]):
        return "Rent Agreement"

    if any(kw in text_lower for kw in ["salary", "designation", "joining date", "employment", "notice period", "ctc"]):
        return "Employment Offer"

    if any(kw in text_lower for kw in ["emi", "loan amount", "interest rate", "repayment", "borrower", "lender"]):
        return "Loan Agreement"

    if any(kw in text_lower for kw in ["warranty", "defect", "replacement", "manufacturer", "guarantee period"]):
        return "Warranty"

    return "General"