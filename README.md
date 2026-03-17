# 📚 AI Lesson Plan Evaluator

An AI-powered tool that evaluates teacher lesson plans across 5 pedagogical dimensions, provides structured feedback, and auto-generates an improved version of the plan. Built for the CenTa Teacher Accreditation context.

---

## 🎯 Problem Statement

Teachers preparing for CenTa accreditation often struggle to get structured, actionable feedback on their lesson plans before formal submission. Without guidance, they repeatedly resubmit plans with the same weaknesses — slowing the accreditation pipeline and reducing teacher confidence.

This tool acts as an intelligent pre-evaluator: teachers get an instant, pedagogically grounded scorecard **and** a ready-to-use improved version of their plan before they submit for formal review.

**Intended User:** Teachers in India preparing for or undergoing CenTa accreditation.

---

## ✨ Features

- **PDF Upload or Text Paste** — flexible lesson plan input
- **5-Dimension AI Evaluation** — scored 1–10 on:
  - Learning Objectives
  - Student Engagement
  - Assessment Strategy
  - Differentiation & Inclusion
  - Curriculum Alignment
- **Structured Feedback** — per-dimension written feedback cards
- **Strengths & Areas for Improvement** — quick summary view
- **AI-Generated Improved Plan** — full rewrite addressing all weaknesses
- **Evaluation History** — all evaluations stored in SQLite, viewable from sidebar

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────┐
│           Streamlit Frontend (app.py)        │
│    Input form · Scorecard · History sidebar  │
└───────────────────┬──────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
  ┌──────▼──────┐     ┌────────▼─────┐
  │ ai_engine   │     │ database.py  │
  │ (Gemini API)│     │ (SQLite)     │
  └──────┬──────┘     └──────────────┘
         │
  ┌──────▼──────────────────────┐
  │   Google OpenRouter (Llama 3.1 70B)     │
  │  Call 1: Evaluate → JSON    │
  │  Call 2: Improve → text     │
  └─────────────────────────────┘
```

### API Flow
1. User fills in teacher name, subject, grade level
2. User pastes lesson text **or** uploads a PDF
3. If PDF → PyMuPDF extracts text from the file
4. `ai_engine.evaluate_lesson_plan()` → structured JSON scores & feedback via Gemini
5. `ai_engine.generate_improved_plan()` → rewritten lesson plan via Gemini
6. `database.save_evaluation()` → full result persisted to SQLite
7. Streamlit renders scorecard, feedback cards, strengths/improvements, and improved plan

### AI Integration Approach
Two separate, purpose-built prompts (not a single generic call):
- **Evaluation prompt** — instructs OpenRouter (Llama 3.1 70B) to return strict JSON with per-dimension scores and feedback
- **Improvement prompt** — instructs Gemini to act as a curriculum designer and rewrite the plan, directly addressing all identified weaknesses

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.9+
- A free OpenRouter API key (get at [aistudio.google.com](https://openrouter.ai))

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/lesson-plan-evaluator.git
cd lesson-plan-evaluator
pip install -r requirements.txt
```

### Set API Key (never hardcode this)

```bash
# Option A — export directly
export OPENROUTER_API_KEY=your_api_key_here

# Option B — use a .env file (recommended)
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
export $(cat .env)
```

### Run

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## 🗂️ Project Structure

```
lesson-plan-evaluator/
├── app.py            # Streamlit UI — main entry point
├── ai_engine.py      # Gemini API calls (evaluate + improve)
├── database.py       # SQLite setup, save, and retrieval
├── requirements.txt  # Python dependencies
├── .env.example      # API key template (safe to commit)
├── .gitignore        # Excludes .env and *.db from git
└── README.md
```

---

## 🤖 AI Development Workflow

| Part | AI-Assisted? | Detail |
|------|-------------|--------|
| Problem framing | Yes | Used Claude to brainstorm domain-relevant ideas; chose final problem myself |
| App scaffolding | Yes | Streamlit layout generated with AI assistance, then reviewed |
| Evaluation prompt | Partial | Iteratively crafted by hand; JSON schema and dimensions defined manually |
| Improvement prompt | Partial | Initial draft AI-assisted; refined manually for tone and specificity |
| Database schema | Yes | Generated and reviewed; column choices made manually |
| CSS styling | Yes | AI-generated base; colours and CenTa branding adjusted manually |
| Error handling | No | Implemented manually after testing edge cases (PDF, short input, JSON parsing) |

---

## ⚠️ Edge Cases & Limitations

| Issue | Impact | Mitigation |
|-------|--------|-----------|
| Very short lesson plans (<50 words) | Low-confidence scores | Warning shown; minimum word check before API call |
| Scanned / image-based PDFs | PyMuPDF extracts no text | Error shown; user prompted to paste text instead |
| Non-English lesson plans | Evaluation prompt is English-only; scores may be unreliable | Future: add language detection + multilingual prompt |
| Vague curriculum alignment | AI scores against general standards, not specific boards | Future: add CBSE / NCERT / IB selector |
| Two sequential API calls | 10–20 second wait on slow connections | Progress spinners shown; future: async calls |
| AI-generated improved plan | May not be accurate for specialist subjects | Disclaimer shown; human review recommended |

---

## 🔮 Future Improvements

- Curriculum framework selector (CBSE, NCERT, IB, Cambridge) to ground alignment scoring
- Multi-teacher dashboard for school administrators
- Score trend charts so teachers can track progress across submissions
- Export evaluation report as a branded PDF
- Human reviewer workflow — allow CenTa evaluators to override AI scores and add comments
- Fine-tune scoring rubric based on CenTa's official accreditation criteria
- Multilingual support (Hindi, Telugu, Tamil)
