import streamlit as st
import json
from database import init_db, save_evaluation, get_all_evaluations, get_evaluation_by_id
from ai_engine import evaluate_lesson_plan, generate_improved_plan, extract_text_from_pdf, DIMENSIONS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Lesson Plan Evaluator",
    page_icon="📚",
    layout="wide"
)

init_db()

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #2563a8 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        text-align: center;
    }
    .score-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 5px solid #2563a8;
        margin-bottom: 1rem;
    }
    .overall-score {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
    }
    .badge-good { color: #16a34a; font-weight: 700; }
    .badge-mid  { color: #d97706; font-weight: 700; }
    .badge-low  { color: #dc2626; font-weight: 700; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a3a5c;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.4rem;
        margin-bottom: 1rem;
    }
    .history-row {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📚 AI Lesson Plan Evaluator</h1>
    <p style="opacity:0.85; margin:0">Powered by OpenRouter (Llama 3.1) · Built for CenTa Teacher Accreditation</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar – History ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ Evaluation History")
    history = get_all_evaluations()
    if not history:
        st.info("No evaluations yet.")
    else:
        for row in history:
            eval_id, ts, name, subject, grade, score = row
            ts_short = ts[:10]
            if st.button(f"📄 {ts_short} | {name} | {subject}", key=f"hist_{eval_id}"):
                st.session_state["view_history"] = eval_id

    st.markdown("---")
    st.caption("CenTa Teacher Accreditation Portal")

# ── History Detail View ───────────────────────────────────────────────────────
if "view_history" in st.session_state:
    eval_id = st.session_state["view_history"]
    row = get_evaluation_by_id(eval_id)
    if row:
        _, ts, name, subject, grade, inp, scores_json, feedback_json, overall, improved = row
        scores   = json.loads(scores_json)
        feedback = json.loads(feedback_json) if isinstance(feedback_json, str) and feedback_json.startswith("{") else {}

        st.markdown(f"## 📋 Past Evaluation — {name} | {subject} | Grade {grade}")
        st.caption(f"Evaluated on {ts[:19]}")

        col1, col2 = st.columns([1, 2])
        with col1:
            colour = "#16a34a" if overall >= 7 else ("#d97706" if overall >= 5 else "#dc2626")
            st.markdown(f"<div class='overall-score' style='color:{colour}'>{overall:.1f}<span style='font-size:1.2rem'>/10</span></div>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;color:#6b7280'>Overall Score</div>", unsafe_allow_html=True)

        with col2:
            for dim, score in scores.items():
                st.markdown(f"**{dim}** — {score}/10")
                st.progress(score / 10)

        with st.expander("📝 View Improved Lesson Plan"):
            st.markdown(improved)

    if st.button("← Back to Evaluator"):
        del st.session_state["view_history"]
        st.rerun()

else:
    # ── Main Evaluation Form ──────────────────────────────────────────────────
    with st.form("eval_form"):
        st.markdown("<div class='section-header'>👤 Teacher & Context</div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            teacher_name = st.text_input("Teacher Name", placeholder="e.g. Priya Sharma")
        with col2:
            subject = st.text_input("Subject", placeholder="e.g. Mathematics")
        with col3:
            grade_level = st.selectbox("Grade Level", [str(i) for i in range(1, 13)] + ["College"])

        st.markdown("<div class='section-header' style='margin-top:1.5rem'>📄 Lesson Plan Input</div>", unsafe_allow_html=True)
        input_mode = st.radio("Input method", ["Paste Text", "Upload PDF"], horizontal=True)

        lesson_text = ""
        uploaded = None
        if input_mode == "Paste Text":
            lesson_text = st.text_area(
                "Paste your lesson plan here",
                height=280,
                placeholder="Write or paste your lesson plan content..."
            )
        else:
            uploaded = st.file_uploader("Upload lesson plan PDF", type=["pdf"])
            if uploaded:
                st.success(f"✅ Uploaded: {uploaded.name}")

        submitted = st.form_submit_button("🔍 Evaluate Lesson Plan", use_container_width=True)

    # ── Processing ────────────────────────────────────────────────────────────
    if submitted:
        # Extract PDF text if needed
        if input_mode == "Upload PDF":
            if not uploaded:
                st.error("Please upload a PDF file.")
                st.stop()
            lesson_text = extract_text_from_pdf(uploaded.read())

        if not lesson_text.strip():
            st.error("Please provide a lesson plan (paste text or upload PDF).")
            st.stop()
        if not teacher_name.strip():
            st.error("Please enter the teacher's name.")
            st.stop()
        if not subject.strip():
            st.error("Please enter the subject.")
            st.stop()
        if len(lesson_text.strip().split()) < 50:
            st.warning("⚠️ Lesson plan seems very short. For best results, provide at least 100 words.")

        # Step 1 – Evaluate
        with st.spinner("🤖 AI is evaluating the lesson plan across 5 dimensions..."):
            try:
                eval_result = evaluate_lesson_plan(lesson_text, subject, grade_level)
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                st.stop()

        scores      = eval_result["scores"]
        feedback    = eval_result["feedback"]
        strengths   = eval_result.get("strengths", [])
        improvements = eval_result.get("areas_for_improvement", [])
        overall_score = round(sum(scores.values()) / len(scores), 1)

        # Step 2 – Generate improved plan
        with st.spinner("✍️ Generating improved lesson plan..."):
            try:
                improved_plan = generate_improved_plan(lesson_text, subject, grade_level, scores, feedback)
            except Exception as e:
                st.error(f"Improvement generation failed: {e}")
                st.stop()

        # Step 3 – Save to DB
        save_evaluation(
            teacher_name, subject, grade_level, lesson_text,
            scores, json.dumps(feedback), overall_score, improved_plan
        )

        # ── Results ───────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(f"## 📊 Evaluation Results — {teacher_name} | {subject} | Grade {grade_level}")

        colour  = "#16a34a" if overall_score >= 7 else ("#d97706" if overall_score >= 5 else "#dc2626")
        verdict = "Strong Plan ✅" if overall_score >= 7 else ("Needs Improvement ⚠️" if overall_score >= 5 else "Significant Revision Needed ❌")

        col_a, col_b = st.columns([1, 3])
        with col_a:
            st.markdown(f"""
            <div style='text-align:center; padding:1.5rem; background:#f8fafc; border-radius:12px; border:2px solid {colour}'>
                <div class='overall-score' style='color:{colour}'>{overall_score}</div>
                <div style='font-size:0.85rem; color:#6b7280'>out of 10</div>
                <div style='font-weight:700; color:{colour}; margin-top:0.5rem'>{verdict}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            st.markdown("<div class='section-header'>Dimension Scores</div>", unsafe_allow_html=True)
            for dim, score in scores.items():
                col_label, col_bar = st.columns([2, 3])
                with col_label:
                    st.markdown(f"**{dim}** — {score}/10")
                with col_bar:
                    st.progress(score / 10)

        # Per-dimension feedback cards
        st.markdown("---")
        st.markdown("### 💬 Detailed Feedback")
        cols = st.columns(2)
        for i, (dim, fb) in enumerate(feedback.items()):
            score = scores[dim]
            with cols[i % 2]:
                icon = "✅" if score >= 7 else ("⚠️" if score >= 5 else "❌")
                st.markdown(f"""
                <div class='score-card'>
                    <strong>{icon} {dim}</strong> &nbsp; <span style='color:#6b7280'>{score}/10</span>
                    <p style='margin-top:0.5rem; color:#374151; font-size:0.9rem'>{fb}</p>
                </div>
                """, unsafe_allow_html=True)

        # Strengths & improvements
        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown("### ✅ Strengths")
            for s in strengths:
                st.markdown(f"- {s}")
        with col_i:
            st.markdown("### 🔧 Areas for Improvement")
            for a in improvements:
                st.markdown(f"- {a}")

        # Improved plan
        st.markdown("---")
        st.markdown("### ✨ AI-Improved Lesson Plan")
        st.info("Based on the evaluation, here is a revised version of your lesson plan:")
        st.markdown(improved_plan)

        st.success("✅ Evaluation saved. View past evaluations in the sidebar.")
