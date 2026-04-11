# Contributing to Verifizer

Thank you for wanting to make Verifizer better.

The single most impactful thing you can contribute is a **skill file** — a markdown file that gives Verifizer domain knowledge about a specific document type. Every skill file added makes the verification smarter for everyone who uses that document type.

You can also contribute bug fixes, improvements to existing agents, or UI enhancements.

---

## What to Contribute

### 1. Skill Files (Highest Impact)

A skill file teaches Verifizer what to look for in a specific document type.

**Document types we need skill files for:**

| Document Type | Filename | Status |
|---|---|---|
| Loan Agreement | `loan_agreement.md` | 🔜 Needed |
| Vehicle Insurance | `vehicle_insurance.md` | 🔜 Needed |
| Warranty Card | `warranty.md` | 🔜 Needed |
| Life Insurance | `life_insurance.md` | 🔜 Needed |
| Franchise Agreement | `franchise_agreement.md` | 🔜 Needed |
| Freelance Contract | `freelance_contract.md` | 🔜 Needed |
| School / College Admission | `admission_agreement.md` | 🔜 Needed |
| Health Insurance — US | `health_insurance_us.md` | 🔜 Needed |
| Tenancy — UK | `rent_agreement_uk.md` | 🔜 Needed |
| Employment — US | `employment_offer_us.md` | 🔜 Needed |

Don't see your document type? Add it. If people sign it and get misled about it, it belongs here.

---

### 2. Bug Fixes

Open an issue first describing the bug, then submit a PR with the fix.

### 3. Agent Improvements

Improvements to prompts, extraction logic, or output formatting are welcome. Open an issue first to discuss before making large changes.

### 4. UI Improvements

Streamlit UI improvements in `app.py` — better layout, clearer output, accessibility fixes.

---

## How to Write a Skill File

Copy this template and fill it in for your document type.

```markdown
# skill: your_document_type.md
# Domain knowledge for [document type] verification
# Used by verification_agent to identify misleading claims

## Purpose
One or two sentences describing what this skill covers.
Which specific documents, geographies, or contexts it applies to.

---

## Red Flags — Claims That Are Almost Always Misleading

- **"Exact phrase agents use"** → What to check in the document instead
- **"Another common claim"** → What the document actually says about this

---

## Critical Clauses to Always Extract from Document

- **Clause name** — what it means and why it matters
- **Another clause** — what to look for

---

## Common Misleading Phrases

| What Is Said | What to Actually Check |
|---|---|
| "Common phrase" | What the document reality usually is |
| "Another phrase" | What to verify |

---

## Consumer Rights — [Country/Region]

- **Right name**: Description of the right and how to use it
- **Escalation**: Where to complain if things go wrong

---

## Known High-Risk Clauses Often Hidden

- Clause type — why it is risky and what to look for
- Another clause — the trap it sets
```

### Rules for Skill Files

**Be specific.** Vague advice like "read the document carefully" helps nobody. Give exact clause names, section numbers where standard, and specific phrases to search for.

**Be accurate.** Only include consumer rights and laws you are certain about. Cite the law or regulation name if possible. Incorrect legal information is worse than no information.

**Be India-first for now.** The existing skill files are India-focused. If you are writing for another country, add the country to the filename — e.g. `health_insurance_us.md`, `rent_agreement_uk.md`.

**No opinions.** Skill files are reference material, not advice. Write what documents typically say, not what people should do about it.

**Keep it readable.** The skill file is read by the AI model as plain text. Use clear headers, bullet points, and tables. Avoid walls of text.

---

## How to Submit

### Step 1 — Fork the repo

```bash
git clone https://github.com/yourusername/verifizer.git
cd verifizer
git checkout -b skill/loan-agreement
```

### Step 2 — Create your skill file

```bash
# Create your file in the skills/ directory
touch skills/loan_agreement.md
```

Fill it in using the template above.

### Step 3 — Test it locally

```bash
# Run Verifizer locally
streamlit run app.py
```

Upload a real document of that type and run a verification. Check that the skill file helps the agent catch at least one misleading claim it would otherwise miss.

### Step 4 — Submit a pull request

Open a PR with:
- The skill file added to `skills/`
- A short description of what document type it covers
- One example of a misleading claim it catches that wasn't caught before

PR title format: `skill: add loan_agreement.md`

---

## Code Contributions

### Setup

```bash
git clone https://github.com/yourusername/verifizer.git
cd verifizer
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
streamlit run app.py
```

### Before submitting a PR

- Test your changes locally end to end
- Make sure existing flows still work — document upload, verification, chat Q&A
- Keep code style consistent with existing files — plain Python, clear comments
- One PR per feature or fix — don't bundle unrelated changes

### Commit message format

```
fix: correct timestamp parsing in whisper_tool
feat: add speaker diarization to audio_agent
skill: add vehicle_insurance.md
docs: update README with deployment instructions
```

---

## What Not to Contribute

- **API keys or credentials** — never commit `.env` or any file with real keys
- **Copyrighted documents** — don't include real policy documents or agreements as examples
- **Unverified legal information** — if you're not sure a law or right is accurate, leave it out
- **Major architecture changes** without opening an issue and discussing first

---

## Questions

Open an issue with the `question` label. Response within a few days.

---

*Every skill file you add helps someone avoid being misled. That's worth the 30 minutes it takes to write one.*