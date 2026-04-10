"""
Verifizer — agents/chat_agent.py
Chat Agent.
Handles interactive Q&A on the loaded document.
Supports both text input (returns text only)
and voice input (returns text + triggers TTS).

The document stays loaded in context for the full session.
Each question is answered strictly based on document content.
"""

import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Model ──────────────────────────────────────────────────────────────────────
CHAT_MODEL = "gpt-4o-mini"    # Q&A task — mini is fast and cheap enough


# ── System prompt ──────────────────────────────────────────────────────────────
CHAT_SYSTEM_PROMPT = """
You are Verifizer, a helpful document assistant.
You have been given a document to analyze — it could be an insurance policy,
rent agreement, employment offer letter, loan agreement, or any contract.

Your job is to answer questions about this document clearly and honestly.

RULES:
- Answer ONLY based on what the document says. Never make up information.
- If the document does not mention something, say so clearly.
- Use plain language. No legal jargon. Write as if explaining to a friend.
- Be direct. Give the answer first, then explain if needed.
- If a question reveals a potential risk or hidden clause for the user, flag it.
- Keep answers concise — 3 to 6 sentences unless a longer answer is genuinely needed.
- If asked about something outside the document (general advice, other topics),
  politely redirect: "I can only answer questions about your uploaded document."
- Never say "As an AI" or "I am a language model." Just answer.

TONE:
- Friendly but factual.
- On the user's side — like a knowledgeable friend reviewing their paperwork.
- Alert them to anything concerning without being alarmist.
""".strip()


# ── Main function ──────────────────────────────────────────────────────────────

def answer_question(
    doc_text: str,
    question: str,
    history: list = None,
    input_mode: str = "text",
) -> str:
    """
    Answer a user question about the loaded document.

    Args:
        doc_text   : full extracted document text from session state
        question   : user's question (text or transcribed voice)
        history    : list of past chat messages for context
                     [{"role": "user"|"assistant", "content": str}]
        input_mode : "text" or "voice" — determines if TTS is triggered
                     (TTS is handled in app.py based on this, not here)

    Returns:
        answer : str — plain text answer to display and/or speak
    """
    if not doc_text or not doc_text.strip():
        return "No document is loaded. Please upload a document first."

    if not question or not question.strip():
        return "Please ask a question about your document."

    try:
        messages = _build_chat_messages(
            doc_text = doc_text,
            question = question,
            history  = history or [],
        )

        response = client.chat.completions.create(
            model       = CHAT_MODEL,
            messages    = messages,
            max_tokens  = 600,
            temperature = 0.3,    # Slightly higher than verification — conversational tone
        )

        answer = response.choices[0].message.content.strip()
        return answer

    except Exception as e:
        return f"Sorry, I couldn't process your question. Error: {str(e)}"


# ── Message builder ────────────────────────────────────────────────────────────

def _build_chat_messages(
    doc_text: str,
    question: str,
    history: list,
) -> list:
    """
    Builds the full messages array for the chat API call.

    Structure:
        [system prompt with document]
        [past conversation history — last N turns]
        [current user question]

    The document is embedded in the system prompt so it stays
    in context for every question without re-sending as user message.
    """
    # ── System message with document embedded ──────────────────────────────────
    system_content = (
        f"{CHAT_SYSTEM_PROMPT}\n\n"
        f"{'=' * 50}\n"
        f"DOCUMENT LOADED FOR THIS SESSION:\n"
        f"{'=' * 50}\n"
        f"{_truncate_for_chat(doc_text)}"
    )

    messages = [{"role": "system", "content": system_content}]

    # ── Recent history (last 6 turns = 3 exchanges) ────────────────────────────
    # Keeps context window manageable without losing recent conversation thread
    recent_history = _get_recent_history(history, max_turns=6)
    for msg in recent_history:
        if msg.get("role") in ("user", "assistant") and msg.get("content"):
            messages.append({
                "role":    msg["role"],
                "content": msg["content"],
            })

    # ── Current question ───────────────────────────────────────────────────────
    messages.append({"role": "user", "content": question})

    return messages


# ── History manager ────────────────────────────────────────────────────────────

def _get_recent_history(history: list, max_turns: int = 6) -> list:
    """
    Returns the last N messages from chat history.
    Filters out messages with audio_bytes key (UI-only field).
    Skips messages without content.

    Args:
        history   : full chat history from session state
        max_turns : max number of messages to include

    Returns:
        Filtered list of {role, content} dicts
    """
    if not history:
        return []

    # Filter to only role + content — strip UI-only fields like audio_bytes
    clean = []
    for msg in history:
        role    = msg.get("role", "")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content and content.strip():
            clean.append({"role": role, "content": content})

    # Return last max_turns messages
    return clean[-max_turns:]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _truncate_for_chat(doc_text: str, max_chars: int = 10000) -> str:
    """
    Truncates document text for chat context.
    Slightly lower limit than verification (10k vs 12k)
    because chat also carries conversation history in context.

    Adds a note if truncated so the model knows.
    """
    if len(doc_text) <= max_chars:
        return doc_text

    return (
        doc_text[:max_chars]
        + "\n\n[Document truncated. Showing first section. "
        + "Some details from later sections may not be available.]"
    )


def is_document_question(question: str) -> bool:
    """
    Heuristic check — is this question likely about the document?
    Used optionally to filter obviously off-topic questions before
    sending to the API.

    Not called by default — the system prompt handles redirection.
    Available for future use.
    """
    off_topic_signals = [
        "weather", "recipe", "joke", "news", "stock",
        "cricket", "movie", "song", "who is", "what is the capital",
    ]
    question_lower = question.lower()
    return not any(signal in question_lower for signal in off_topic_signals)


def format_answer_for_voice(answer: str) -> str:
    """
    Prepares an answer for TTS conversion.
    Removes markdown and shortens if needed.
    Called in app.py before passing to tts_tool.

    Args:
        answer : raw answer string from answer_question()

    Returns:
        Cleaned string suitable for speaking aloud.
    """
    import re

    # Remove markdown bold/italic
    answer = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", answer)

    # Remove markdown headers
    answer = re.sub(r"^#{1,6}\s+", "", answer, flags=re.MULTILINE)

    # Replace bullet points with natural pause
    answer = re.sub(r"^\s*[-•]\s+", "", answer, flags=re.MULTILINE)

    # Collapse newlines
    answer = re.sub(r"\n+", ". ", answer)
    answer = re.sub(r"\s{2,}", " ", answer)

    # Cap at ~500 chars for voice — longer answers get cut off naturally
    if len(answer) > 500:
        answer = answer[:497] + "..."

    return answer.strip()