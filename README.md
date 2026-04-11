# Verifizer
### Did they tell you the truth?

Upload any document. Upload the call recording or type what you were told. Verifizer cross-checks every claim against the actual document and tells you exactly where the truth ends.

---

## The Problem

Every day, millions of people sign documents they don't fully understand — after being told something different by an agent, HR, landlord, or salesperson.

> *"This policy covers everything."*
> *"No waiting period for pre-existing conditions."*
> *"Security deposit is fully refundable."*
> *"Bonus is guaranteed every year."*

By the time you find out the truth, it's too late. The document you signed says something else entirely.

**Verifizer exists to close that gap — before you sign, or after.**

---

## What It Does

```
You upload                         Verifizer tells you
─────────────────────────────      ──────────────────────────────────────
📄 Insurance policy PDF      →     ✗ FALSE: Agent said no waiting period.
🎙️ Call recording with agent  →         Document shows 2-year PED waiting.
                                         [Clause 4.2 · Timestamp 2:14]

📄 Offer letter              →     ⚠ MISLEADING: "Bonus guaranteed" but
⌨️  "HR said bonus every year" →        document says "at company's discretion"
                                         [Section 7.3]

📄 Rent agreement            →     ✓ HONEST: 2-month security deposit
⌨️  "Deposit is 2 months"    →          confirmed in Clause 2.1
```

---

## Features

- **Document upload** — PDF, scanned image, or photo of any document
- **Audio upload** — upload a recorded call or voice note for transcription
- **Typed claims** — type what you were told if you have no recording
- **Verdict per claim** — Honest / Misleading / False with clause reference and audio timestamp
- **Ask your document** — interactive text Q&A on any loaded document
- **Skills architecture** — modular domain knowledge files for different document types
- **Multilingual** — handles documents and audio in any language
- **Privacy by design** — no documents stored, no accounts required, no data retained

---

## Architecture

Verifizer uses a multi-agent architecture where each agent has a single responsibility.

```
USER INPUT
├── 📄 Document (PDF / Image)
├── 🎙️ Audio Recording (uploaded call)
└── ⌨️  Typed Claims

            ↓

┌─────────────────────────────────────────┐
│           ORCHESTRATOR                  │
│   Routes input → decides agent order   │
└──────┬──────────┬──────────┬────────────┘
       ↓          ↓          ↓
┌──────────┐ ┌─────────┐ ┌──────────┐
│ DOCUMENT │ │  AUDIO  │ │  CLAIMS  │
│  AGENT   │ │  AGENT  │ │  AGENT   │
│          │ │         │ │          │
│ GPT-4o   │ │ Whisper │ │GPT-4o    │
│ Vision   │ │ API     │ │mini      │
│ extracts │ │ tran-   │ │extracts  │
│ clauses  │ │ scribes │ │promises  │
└────┬─────┘ └────┬────┘ └────┬─────┘
     └────────────┴────────────┘
                  ↓
     ┌────────────────────────┐
     │      SKILLS LAYER      │
     │  health_insurance.md   │
     │  rent_agreement.md     │
     │  employment_offer.md   │
     │  loan_agreement.md     │
     └────────────┬───────────┘
                  ↓
     ┌────────────────────────┐
     │   VERIFICATION AGENT   │
     │                        │
     │  Claims vs Document    │
     │  Verdict per claim     │
     │  Clause references     │
     │  Audio timestamps      │
     └────────────┬───────────┘
                  ↓
     ┌────────────────────────┐
     │     CHAT AGENT         │
     │  Interactive Q&A on    │
     │  loaded document       │
     └────────────────────────┘
```

### Why This Architecture

| Component | Technology | Why |
|---|---|---|
| Document parsing | GPT-4o Vision | Handles text PDFs, scanned PDFs, and photos |
| Audio transcription | OpenAI Whisper | Near-perfect accuracy, timestamps, multilingual |
| Claims extraction | GPT-4o-mini | Structured extraction — cheap and fast enough |
| Verification reasoning | GPT-4o | Deep reasoning — quality matters here |
| Interactive Q&A | GPT-4o-mini | Conversational — mini handles this well |
| Skills files | Plain Markdown | Human-readable, community-contributable |

---

## Skills.md Architecture

The Skills system is what makes Verifizer extensible and community-driven.

Each skill file is a plain markdown document that contains:
- Red flags specific to that document type
- Common misleading phrases used in that industry
- Critical clauses to look for
- Consumer rights and legal protections

The verification agent reads the relevant skill file as part of its context — giving it domain expertise without any retraining.

```
skills/
├── health_insurance.md    ← knows IRDAI rules, waiting period traps, sub-limits
├── rent_agreement.md      ← knows lock-in tricks, deposit deductions, rent escalation
├── employment_offer.md    ← knows CTC vs in-hand gap, clawback clauses, non-competes
└── loan_agreement.md      ← coming soon
```

**Want to add a skill? Read [CONTRIBUTING.md](CONTRIBUTING.md) and open a PR.**

---

## Tech Stack

```
Language        Python 3.10+
UI              Streamlit
Document AI     GPT-4o Vision (OpenAI)
Audio           OpenAI Whisper
Verification    GPT-4o (OpenAI)
Chat Q&A        GPT-4o-mini (OpenAI)
TTS             gTTS (free)
PDF parsing     PyMuPDF
Hosting         Streamlit Cloud (free)
Storage         None — privacy by design
```

**Single API key.** Everything runs on one OpenAI key.

---

## Getting Started

### Try it instantly
👉 **[Live Demo](https://your-streamlit-url.streamlit.app)** — works in browser, no install needed.

### Run locally

**Prerequisites:**
- Python 3.10+
- OpenAI API key
- ffmpeg installed (`winget install ffmpeg` on Windows, `brew install ffmpeg` on Mac)

```bash
# 1. Clone the repo
git clone https://github.com/Arsalan3043/verifizer.git
cd verifizer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run
streamlit run app.py
```

### Environment variables

Create a `.env` file in the root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Project Structure

```
verifizer/
├── app.py                        ← Streamlit UI entry point
├── requirements.txt
├── .env                          ← your API key (never commit)
│
├── agents/
│   ├── orchestrator.py           ← routes all flows between agents
│   ├── document_agent.py         ← GPT-4o Vision document extraction
│   ├── audio_agent.py            ← Whisper transcription
│   ├── claims_agent.py           ← extracts spoken promises
│   ├── verification_agent.py     ← cross-checks claims vs document
│   └── chat_agent.py             ← interactive Q&A on document
│
├── tools/
│   ├── vision_tool.py            ← GPT-4o Vision API wrapper
│   ├── whisper_tool.py           ← Whisper API wrapper
│   └── tts_tool.py               ← gTTS text-to-speech wrapper
│
├── skills/
│   ├── health_insurance.md       ← domain knowledge: health insurance
│   ├── rent_agreement.md         ← domain knowledge: rent agreements
│   └── employment_offer.md       ← domain knowledge: offer letters
│
└── utils/
    ├── file_handler.py           ← upload handling, PDF extraction
    └── session_state.py          ← Streamlit session management
```

---

## Supported Document Types

| Document | Skill File | Status |
|---|---|---|
| Health Insurance Policy | `health_insurance.md` | ✅ Available |
| Rent / Lease Agreement | `rent_agreement.md` | ✅ Available |
| Employment Offer Letter | `employment_offer.md` | ✅ Available |
| Loan Agreement | `loan_agreement.md` | 🔜 Coming soon |
| Vehicle Insurance | `vehicle_insurance.md` | 🔜 Coming soon |
| Warranty Card | `warranty.md` | 🔜 Coming soon |
| General Documents | — | ✅ Works without skill file |

---

## Cost Estimate

Verifizer is designed to be near-zero cost for personal and demo use.

| Action | Model | Approx Cost |
|---|---|---|
| Parse a 2-page PDF | GPT-4o Vision | ~$0.02 |
| Transcribe 5 min audio | Whisper | ~$0.03 |
| Extract claims | GPT-4o-mini | ~$0.01 |
| Run verification | GPT-4o | ~$0.04 |
| Chat question | GPT-4o-mini | ~$0.01 |
| **Full session** | | **~$0.10–0.15** |

Roughly ₹10–15 per full verification session.

---

## Contributing

Contributions are welcome — especially new skill files.

**The easiest way to contribute:**

1. Pick a document type that isn't covered yet
2. Copy `skills/health_insurance.md` as a template
3. Fill in the red flags, misleading phrases, and consumer rights for your domain
4. Open a PR

Every skill file added makes Verifizer smarter for everyone.

Read [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## Roadmap

- [x] Document upload and parsing (PDF + image)
- [x] Audio upload and transcription (Whisper)
- [x] Claim extraction from transcript and typed input
- [x] Verification with clause references and timestamps
- [x] Interactive text Q&A on document
- [x] Skills.md architecture
- [ ] Live mic Q&A (voice-in, voice-out)
- [ ] Loan agreement skill file
- [ ] RAG for large documents (10+ pages)
- [ ] Multilingual UI
- [ ] Mobile PWA (Next.js + FastAPI)
- [ ] Community skill file contributions

---

## Disclaimer

Verifizer is an AI-assisted tool for informational purposes only. It is not a substitute for legal advice. Verdicts are based on AI reasoning and may not be fully accurate. Always consult a qualified professional for legal or financial decisions.

Recording laws vary by jurisdiction. Ensure you have the right to record any call before uploading it.

---

## License

MIT License — free to use, modify, and distribute.

---

*Built with Python · OpenAI · Streamlit · Skills.md*
