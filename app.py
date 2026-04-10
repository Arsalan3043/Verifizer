"""
Verifizer — app.py
Main Streamlit entry point.
Upload a document + audio/text → find out if what was said matches what was signed.
"""

import streamlit as st
from dotenv import load_dotenv
from utils.session_state import init_session_state
from utils.file_handler import handle_document_upload, handle_audio_upload

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Verifizer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

/* ── Root theme ── */
:root {
    --bg:        #0d0d0d;
    --surface:   #141414;
    --border:    #2a2a2a;
    --accent:    #e8ff47;
    --accent2:   #ff4747;
    --text:      #f0f0f0;
    --muted:     #666;
    --honest:    #47ff8a;
    --mislead:   #ffb347;
    --false:     #ff4747;
}

/* ── Global resets ── */
html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem !important; max-width: 1100px; margin: auto; }

/* ── Header ── */
.vf-header {
    display: flex;
    align-items: baseline;
    gap: 1rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2.5rem;
}
.vf-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2.4rem;
    color: var(--accent);
    letter-spacing: -1px;
    line-height: 1;
}
.vf-tagline {
    font-size: 0.78rem;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── Mode tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    gap: 0 !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
    padding: 0.5rem 1.2rem !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: #000 !important;
    font-weight: 600 !important;
}

/* ── Upload boxes ── */
.upload-zone {
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    background: var(--surface);
    margin-bottom: 1rem;
}
.upload-label {
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

/* ── Streamlit file uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"] label { color: var(--muted) !important; font-size: 0.8rem !important; }
[data-testid="stFileDropzoneInstructions"] { color: var(--muted) !important; }

/* ── Text inputs ── */
textarea, .stTextArea textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.85rem !important;
}
textarea:focus { border-color: var(--accent) !important; outline: none !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.6rem 2rem !important;
    width: 100% !important;
    transition: opacity 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover { opacity: 0.85 !important; }

/* ── Secondary button ── */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 0.5rem 1.2rem !important;
}

/* ── Document parsed status bar ── */
.doc-status {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Verdict cards ── */
.verdict-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
}
.verdict-honest  { border-left: 4px solid var(--honest); }
.verdict-mislead { border-left: 4px solid var(--mislead); }
.verdict-false   { border-left: 4px solid var(--false); }

.verdict-tag {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 3px;
    display: inline-block;
    margin-bottom: 0.5rem;
}
.tag-honest  { background: #47ff8a22; color: var(--honest); }
.tag-mislead { background: #ffb34722; color: var(--mislead); }
.tag-false   { background: #ff474722; color: var(--false); }

.verdict-claim   { font-size: 0.88rem; color: var(--text); margin-bottom: 0.4rem; }
.verdict-ref     { font-size: 0.75rem; color: var(--muted); }
.verdict-summary { font-size: 0.82rem; color: var(--text); line-height: 1.6; }

/* ── Chat messages ── */
.chat-msg {
    padding: 0.8rem 1rem;
    border-radius: 6px;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
    line-height: 1.6;
}
.chat-user {
    background: #1a1a1a;
    border: 1px solid var(--border);
    color: var(--text);
    margin-left: 2rem;
}
.chat-ai {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    color: var(--text);
    margin-right: 2rem;
}
.chat-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 0.3rem;
}

/* ── Section headers ── */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    color: var(--muted);
    margin-bottom: 0.8rem;
    margin-top: 1.5rem;
}

/* ── Spinner / loading ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Alerts ── */
.stAlert { background: var(--surface) !important; border-color: var(--border) !important; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────────────────────
init_session_state()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vf-header">
    <span class="vf-logo">Verifizer</span>
    <span class="vf-tagline">Did they tell you the truth?</span>
</div>
""", unsafe_allow_html=True)


# ── Document upload (always visible, top of page) ─────────────────────────────
st.markdown('<div class="section-title">Step 1 — Upload Your Document</div>', unsafe_allow_html=True)

col_upload, col_status = st.columns([2, 1])

with col_upload:
    doc_file = st.file_uploader(
        "PDF, image, or photo of document",
        type=["pdf", "png", "jpg", "jpeg"],
        key="doc_uploader",
        label_visibility="collapsed",
    )

with col_status:
    if st.session_state.doc_parsed and st.session_state.doc_text:
        st.markdown(f"""
        <div class="doc-status">
            ✅ Document ready — {st.session_state.doc_filename}
        </div>
        """, unsafe_allow_html=True)

        # Skill selector shown only after doc is loaded
        st.markdown('<div class="section-title">Document Type</div>', unsafe_allow_html=True)
        skill_choice = st.selectbox(
            "Document type",
            options=["Auto-detect", "Health Insurance", "Rent Agreement", "Employment Offer", "Loan Agreement", "General"],
            key="skill_choice",
            label_visibility="collapsed",
        )
    else:
        st.markdown("""
        <div class="doc-status" style="border-left-color: #2a2a2a;">
            ○ No document loaded yet
        </div>
        """, unsafe_allow_html=True)

# ── Parse document on upload ───────────────────────────────────────────────────
if doc_file and not st.session_state.doc_parsed:
    with st.spinner("Reading document..."):
        success, result = handle_document_upload(doc_file)
        if success:
            st.session_state.doc_text     = result["text"]
            st.session_state.doc_filename = result["filename"]
            st.session_state.doc_type     = result["type"]
            st.session_state.doc_parsed   = True
            st.rerun()
        else:
            st.error(f"Could not read document: {result}")


st.markdown("---")


# ── Main modes (only active when document is loaded) ──────────────────────────
if not st.session_state.doc_parsed:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 0; color: #444;">
        <div style="font-size:2rem; margin-bottom:1rem;">↑</div>
        <div style="font-family:'Syne',sans-serif; font-size:1rem; font-weight:600;">
            Upload a document to get started
        </div>
        <div style="font-size:0.78rem; margin-top:0.5rem; color:#333;">
            Insurance policy · Rent agreement · Offer letter · Loan document · Any contract
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    st.markdown('<div class="section-title">Step 2 — Choose What You Want To Do</div>', unsafe_allow_html=True)

    tab_verify, tab_chat = st.tabs(["🔍  Verify Claims", "💬  Ask Document"])

    # ── TAB 1: VERIFY ──────────────────────────────────────────────────────────
    with tab_verify:
        st.markdown('<div class="section-title">What were you told?</div>', unsafe_allow_html=True)

        verify_col1, verify_col2 = st.columns(2)

        with verify_col1:
            # Audio upload
            st.markdown('<div class="upload-label">Upload call / voice recording (optional)</div>', unsafe_allow_html=True)
            audio_file = st.file_uploader(
                "Audio recording",
                type=["mp3", "wav", "m4a", "ogg"],
                key="audio_uploader",
                label_visibility="collapsed",
            )
            if audio_file:
                st.audio(audio_file)

        with verify_col2:
            # Typed claims
            st.markdown('<div class="upload-label">Or type what you were told (optional)</div>', unsafe_allow_html=True)
            typed_claims = st.text_area(
                "Typed claims",
                placeholder="e.g. Agent said: covers all hospitalization, no waiting period, cashless everywhere...",
                height=120,
                key="typed_claims",
                label_visibility="collapsed",
            )

        # Live mic (collapsible)
        with st.expander("🎤  Record voice directly instead"):
            st.info("Live mic recording coming in V2. Use audio upload or type claims above.")

        st.markdown("")

        # Verify button
        verify_ready = audio_file or (typed_claims and typed_claims.strip())
        if st.button("Run Verification →", type="primary", disabled=not verify_ready, key="btn_verify"):
            with st.spinner("Analyzing..."):
                from agents.orchestrator import run_verification
                result = run_verification(
                    doc_text    = st.session_state.doc_text,
                    skill       = st.session_state.get("skill_choice", "Auto-detect"),
                    audio_file  = audio_file,
                    typed_claims= typed_claims,
                )
                st.session_state.verification_result = result

        if not verify_ready:
            st.caption("Upload a recording or type what you were told to run verification.")

        # ── Verification results ───────────────────────────────────────────────
        if st.session_state.verification_result:
            st.markdown("---")
            st.markdown('<div class="section-title">Verification Results</div>', unsafe_allow_html=True)

            result = st.session_state.verification_result

            # Overall verdict banner
            total     = result.get("total", 0)
            honest    = result.get("honest_count", 0)
            mislead   = result.get("mislead_count", 0)
            false_c   = result.get("false_count", 0)

            banner_color = "#47ff8a" if false_c == 0 and mislead == 0 else ("#ffb347" if false_c == 0 else "#ff4747")
            banner_label = "LOOKS HONEST" if false_c == 0 and mislead == 0 else ("SOME MISLEADING CLAIMS" if false_c == 0 else "FALSE CLAIMS FOUND")

            st.markdown(f"""
            <div style="background:var(--surface); border:1px solid {banner_color}33;
                        border-left: 4px solid {banner_color}; border-radius:8px;
                        padding:1rem 1.4rem; margin-bottom:1.5rem; display:flex;
                        justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-family:'Syne',sans-serif; font-size:1.1rem;
                                font-weight:800; color:{banner_color}; letter-spacing:-0.5px;">
                        {banner_label}
                    </div>
                    <div style="font-size:0.75rem; color:var(--muted); margin-top:0.2rem;">
                        {total} claims checked
                    </div>
                </div>
                <div style="display:flex; gap:1.5rem; font-size:0.78rem; text-align:center;">
                    <div><div style="color:#47ff8a; font-weight:700; font-size:1.2rem;">{honest}</div><div style="color:var(--muted);">Honest</div></div>
                    <div><div style="color:#ffb347; font-weight:700; font-size:1.2rem;">{mislead}</div><div style="color:var(--muted);">Misleading</div></div>
                    <div><div style="color:#ff4747; font-weight:700; font-size:1.2rem;">{false_c}</div><div style="color:var(--muted);">False</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Individual claim cards
            for item in result.get("claims", []):
                verdict  = item.get("verdict", "honest").lower()
                css_card = f"verdict-{verdict if verdict in ['honest','mislead','false'] else 'honest'}"
                css_tag  = f"tag-{verdict if verdict in ['honest','mislead','false'] else 'honest'}"
                label    = {"honest": "✓ Honest", "mislead": "⚠ Misleading", "false": "✗ False"}.get(verdict, verdict)

                timestamp = f" · 🎙 {item['timestamp']}" if item.get("timestamp") else ""
                clause    = f"📄 {item['clause_ref']}" if item.get("clause_ref") else ""

                st.markdown(f"""
                <div class="verdict-card {css_card}">
                    <span class="verdict-tag {css_tag}">{label}</span>
                    <div class="verdict-claim">"{item.get('claim','')}"</div>
                    <div class="verdict-summary">{item.get('explanation','')}</div>
                    <div class="verdict-ref">{clause}{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)

            # Summary note
            if result.get("summary_note"):
                st.markdown(f"""
                <div style="background:var(--surface); border:1px solid var(--border);
                            border-radius:6px; padding:1rem 1.2rem; margin-top:1rem;
                            font-size:0.82rem; color:var(--muted); line-height:1.7;">
                    💡 {result['summary_note']}
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 2: ASK DOCUMENT ────────────────────────────────────────────────────
    with tab_chat:
        st.markdown('<div class="section-title">Ask anything about your document</div>', unsafe_allow_html=True)

        # Chat history display
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-msg chat-user">
                        <div class="chat-label">You</div>
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-msg chat-ai">
                        <div class="chat-label">Verifizer</div>
                        {msg["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                    # Play audio if this is a voice response
                    if msg.get("audio_bytes"):
                        st.audio(msg["audio_bytes"], format="audio/mp3")

        else:
            st.markdown("""
            <div style="color:var(--muted); font-size:0.82rem; padding:1rem 0;">
                Ask any question about your document. Examples:<br><br>
                · "What is not covered in this policy?"<br>
                · "What happens if I miss an EMI?"<br>
                · "What are my notice period obligations?"<br>
                · "Are there any hidden charges mentioned?"
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Text input + send
        chat_col1, chat_col2 = st.columns([5, 1])

        with chat_col1:
            user_question = st.text_area(
                "Ask a question",
                placeholder="What does this document say about...",
                height=80,
                key="chat_input",
                label_visibility="collapsed",
            )

        with chat_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            send_text = st.button("Send →", type="primary", key="btn_chat_text")

        # Voice input placeholder
        with st.expander("🎤  Ask by voice instead"):
            st.info("Voice Q&A coming in V2. Type your question above for now.")

        # Handle text question
        if send_text and user_question and user_question.strip():
            from agents.chat_agent import answer_question
            with st.spinner("Reading document..."):
                answer = answer_question(
                    doc_text = st.session_state.doc_text,
                    question = user_question.strip(),
                    history  = st.session_state.chat_history,
                )
                st.session_state.chat_history.append({"role": "user",      "content": user_question.strip()})
                st.session_state.chat_history.append({"role": "assistant", "content": answer, "audio_bytes": None})
                st.rerun()

        # Clear chat
        if st.session_state.chat_history:
            if st.button("Clear chat", type="secondary", key="btn_clear_chat"):
                st.session_state.chat_history = []
                st.rerun()