import json
import os
import urllib.request

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL   = "openrouter/auto"

DIMENSIONS = [
    "Learning Objectives",
    "Student Engagement",
    "Assessment Strategy",
    "Differentiation & Inclusion",
    "Curriculum Alignment"
]

EVALUATION_PROMPT = """You are an expert pedagogical evaluator working for a teacher accreditation body.

Evaluate the following lesson plan across exactly these 5 dimensions:
1. Learning Objectives – Are they clear, measurable, and student-centered?
2. Student Engagement – Are activities interactive and varied?
3. Assessment Strategy – Is there formative/summative assessment built in?
4. Differentiation & Inclusion – Does it address different learning needs?
5. Curriculum Alignment – Does it align with standard curriculum goals?

Subject: {subject}
Grade Level: {grade_level}

Lesson Plan:
{lesson_plan}

Respond with ONLY valid JSON. No markdown, no explanation, no code fences. Exact format:
{{
  "scores": {{
    "Learning Objectives": <integer 1-10>,
    "Student Engagement": <integer 1-10>,
    "Assessment Strategy": <integer 1-10>,
    "Differentiation & Inclusion": <integer 1-10>,
    "Curriculum Alignment": <integer 1-10>
  }},
  "feedback": {{
    "Learning Objectives": "<specific 2-3 sentence feedback>",
    "Student Engagement": "<specific 2-3 sentence feedback>",
    "Assessment Strategy": "<specific 2-3 sentence feedback>",
    "Differentiation & Inclusion": "<specific 2-3 sentence feedback>",
    "Curriculum Alignment": "<specific 2-3 sentence feedback>"
  }},
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "areas_for_improvement": ["<area 1>", "<area 2>", "<area 3>"]
}}"""

IMPROVEMENT_PROMPT = """You are an expert curriculum designer. Based on the evaluation feedback below,
rewrite and improve the following lesson plan.

Subject: {subject}
Grade Level: {grade_level}

Original Lesson Plan:
{lesson_plan}

Evaluation Feedback:
{feedback}

Scores:
{scores}

Write a complete, improved lesson plan that directly addresses all identified weaknesses.
Structure it clearly with these sections:
- Objectives
- Materials
- Introduction (Hook)
- Main Activity
- Assessment
- Differentiation

Make it practical and immediately usable in a classroom."""


def _call_openrouter(prompt: str) -> str:
    """Make a single call to OpenRouter and return the response text."""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://lesson-plan-evaluator.app",
            "X-Title": "Lesson Plan Evaluator"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF file using PyMuPDF."""
    import fitz
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def evaluate_lesson_plan(lesson_plan_text: str, subject: str, grade_level: str) -> dict:
    """
    Send lesson plan to OpenRouter for structured evaluation.
    Returns a dict with scores, feedback, strengths, areas_for_improvement.
    """
    prompt = EVALUATION_PROMPT.format(
        subject=subject,
        grade_level=grade_level,
        lesson_plan=lesson_plan_text
    )
    raw = _call_openrouter(prompt)

    # Strip markdown code fences if model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def generate_improved_plan(lesson_plan_text: str, subject: str, grade_level: str,
                           scores: dict, feedback: dict) -> str:
    """
    Send evaluation results to OpenRouter and get a rewritten improved lesson plan.
    """
    scores_str   = "\n".join([f"- {k}: {v}/10" for k, v in scores.items()])
    feedback_str = "\n".join([f"- {k}: {v}" for k, v in feedback.items()])

    prompt = IMPROVEMENT_PROMPT.format(
        subject=subject,
        grade_level=grade_level,
        lesson_plan=lesson_plan_text,
        feedback=feedback_str,
        scores=scores_str
    )
    return _call_openrouter(prompt)
