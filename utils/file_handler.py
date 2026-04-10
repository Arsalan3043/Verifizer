"""
Verifizer — utils/file_handler.py
Handles uploaded files — detects type, extracts text from PDFs,
prepares images for Vision API, validates audio filess.
"""

import io
import base64
from pathlib import Path

import fitz          # PyMuPDF
from PIL import Image


# ── Supported types ────────────────────────────────────────────────────────────
SUPPORTED_DOC_TYPES   = {"pdf", "png", "jpg", "jpeg"}
SUPPORTED_AUDIO_TYPES = {"mp3", "wav", "m4a", "ogg"}

# Max file sizes
MAX_DOC_SIZE_MB   = 20
MAX_AUDIO_SIZE_MB = 25


# ── Document handler ───────────────────────────────────────────────────────────

def handle_document_upload(uploaded_file) -> tuple[bool, dict | str]:
    """
    Entry point called from app.py when user uploads a document.

    Returns:
        (True,  {"text": str, "filename": str, "type": str, "image_b64": str|None})
        (False, "error message string")
    """
    try:
        filename  = uploaded_file.name
        extension = Path(filename).suffix.lower().lstrip(".")
        size_mb   = uploaded_file.size / (1024 * 1024)

        # ── Size check ────────────────────────────────────────
        if size_mb > MAX_DOC_SIZE_MB:
            return False, f"File too large ({size_mb:.1f} MB). Max {MAX_DOC_SIZE_MB} MB."

        # ── Type check ────────────────────────────────────────
        if extension not in SUPPORTED_DOC_TYPES:
            return False, f"Unsupported file type: .{extension}"

        file_bytes = uploaded_file.read()

        # ── Route by type ─────────────────────────────────────
        if extension == "pdf":
            text, image_b64 = _process_pdf(file_bytes)
        else:
            text, image_b64 = _process_image(file_bytes, extension)

        if not text and not image_b64:
            return False, "Could not extract content from this file."

        return True, {
            "text":      text,
            "filename":  filename,
            "type":      "pdf" if extension == "pdf" else "image",
            "image_b64": image_b64,   # Used by Vision API if text extraction is poor
        }

    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def _process_pdf(file_bytes: bytes) -> tuple[str, str | None]:
    """
    Extract text from PDF using PyMuPDF.
    If text is sparse (scanned PDF), also render first page as image
    so GPT-4o Vision can read it.

    Returns:
        (extracted_text, base64_image_of_first_page | None)
    """
    text_parts = []
    image_b64  = None

    pdf = fitz.open(stream=file_bytes, filetype="pdf")

    for page_num, page in enumerate(pdf):
        page_text = page.get_text("text").strip()
        if page_text:
            text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

    full_text = "\n\n".join(text_parts)

    # If extracted text is very short → likely a scanned PDF
    # Render first page as image for Vision fallback
    if len(full_text.strip()) < 200:
        first_page = pdf[0]
        mat        = fitz.Matrix(2.0, 2.0)        # 2x zoom for clarity
        pix        = first_page.get_pixmap(matrix=mat)
        img_bytes  = pix.tobytes("png")
        image_b64  = base64.b64encode(img_bytes).decode("utf-8")

    pdf.close()
    return full_text, image_b64


def _process_image(file_bytes: bytes, extension: str) -> tuple[str, str]:
    """
    Convert uploaded image to base64 for GPT-4o Vision.
    Returns empty string for text (Vision will read it),
    and base64 string for the image.
    """
    # Validate it's a real image
    img = Image.open(io.BytesIO(file_bytes))
    img.verify()

    # Re-open after verify (verify closes the file)
    img = Image.open(io.BytesIO(file_bytes))

    # Convert to RGB if needed (removes alpha channel issues)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Re-encode to JPEG for smaller payload
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    image_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return "", image_b64   # text is empty — Vision API will read the image


# ── Audio handler ──────────────────────────────────────────────────────────────

def handle_audio_upload(uploaded_file) -> tuple[bool, dict | str]:
    """
    Validates and prepares uploaded audio for Whisper transcription.

    Returns:
        (True,  {"bytes": bytes, "filename": str, "extension": str})
        (False, "error message string")
    """
    try:
        filename  = uploaded_file.name
        extension = Path(filename).suffix.lower().lstrip(".")
        size_mb   = uploaded_file.size / (1024 * 1024)

        # ── Size check ────────────────────────────────────────
        if size_mb > MAX_AUDIO_SIZE_MB:
            return False, f"Audio too large ({size_mb:.1f} MB). Max {MAX_AUDIO_SIZE_MB} MB."

        # ── Type check ────────────────────────────────────────
        if extension not in SUPPORTED_AUDIO_TYPES:
            return False, f"Unsupported audio type: .{extension}"

        audio_bytes = uploaded_file.read()

        return True, {
            "bytes":     audio_bytes,
            "filename":  filename,
            "extension": extension,
        }

    except Exception as e:
        return False, f"Error reading audio file: {str(e)}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_file_extension(filename: str) -> str:
    """Returns lowercase extension without dot. e.g. 'pdf', 'mp3'"""
    return Path(filename).suffix.lower().lstrip(".")


def is_scanned_pdf(text: str) -> bool:
    """
    Heuristic: if extracted text is very short,
    the PDF is likely scanned and needs Vision.
    """
    return len(text.strip()) < 200


def truncate_text(text: str, max_chars: int = 12000) -> str:
    """
    Truncates document text to stay within token limits.
    12000 chars ≈ ~3000 tokens — safe for GPT-4o context.
    Adds a note if truncated so the model knows.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[Document truncated for processing. Showing first section only.]"