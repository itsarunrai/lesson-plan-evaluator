import sqlite3
import json
from datetime import datetime

DB_PATH = "evaluations.db"


def init_db():
    """Create the evaluations table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT,
            teacher_name TEXT,
            subject      TEXT,
            grade_level  TEXT,
            input_text   TEXT,
            scores       TEXT,
            feedback     TEXT,
            overall_score REAL,
            improved_plan TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_evaluation(teacher_name: str, subject: str, grade_level: str,
                    input_text: str, scores: dict, feedback: str,
                    overall_score: float, improved_plan: str):
    """Persist one evaluation result to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO evaluations
        (timestamp, teacher_name, subject, grade_level, input_text,
         scores, feedback, overall_score, improved_plan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        teacher_name,
        subject,
        grade_level,
        input_text,
        json.dumps(scores),
        feedback,
        overall_score,
        improved_plan
    ))
    conn.commit()
    conn.close()


def get_all_evaluations() -> list:
    """Return summary rows for the sidebar history list."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, teacher_name, subject, grade_level, overall_score
        FROM evaluations
        ORDER BY timestamp DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_evaluation_by_id(eval_id: int) -> tuple:
    """Return a full evaluation row by its ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,))
    row = c.fetchone()
    conn.close()
    return row
