"""
================================================================================
  database/db.py  –  SQLite schema & helper utilities
================================================================================

  Tables
  ------
  educators   : registered educators (username / password hash)
  students    : every student attempt record
  quizzes     : quiz metadata, linked to an educator via educator_id
  questions   : individual questions linked to a quiz
  results     : final score per student-quiz pair

  All foreign-key constraints are enforced by PRAGMA foreign_keys = ON.
================================================================================
"""

import sqlite3
import hashlib
import os

# Path to the SQLite file  (auto-created on first run)
DB_PATH = os.path.join(os.path.dirname(__file__), "quiz.db")


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def get_connection():
    """Return a new SQLite connection with row_factory=sqlite3.Row so that
    columns can be accessed by name (row['column']) as well as by index."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")   # enforce FK constraints
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation  (called once at startup)
# ---------------------------------------------------------------------------

def init_db():
    """Create all tables if they do not already exist."""
    conn = get_connection()
    cur  = conn.cursor()

    # ── Educators ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS educators (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,          -- SHA-256 hex digest
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Quizzes ────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            educator_id   INTEGER NOT NULL REFERENCES educators(id),
            title         TEXT    NOT NULL,
            quiz_code     TEXT    NOT NULL UNIQUE,  -- 6-char alphanumeric
            total_marks   INTEGER NOT NULL DEFAULT 0,
            duration_mins INTEGER NOT NULL DEFAULT 30,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure existing quizzes table has duration_mins column
    existing_columns = [row[1] for row in conn.execute("PRAGMA table_info(quizzes)").fetchall()]
    if "duration_mins" not in existing_columns:
        conn.execute("ALTER TABLE quizzes ADD COLUMN duration_mins INTEGER NOT NULL DEFAULT 30")

    # ── Questions ──────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id        INTEGER NOT NULL REFERENCES quizzes(id),
            question_text  TEXT    NOT NULL,
            option_a       TEXT    NOT NULL,
            option_b       TEXT    NOT NULL,
            option_c       TEXT    NOT NULL,
            option_d       TEXT    NOT NULL,
            correct_option TEXT    NOT NULL CHECK(correct_option IN ('A','B','C','D')),
            marks          INTEGER NOT NULL DEFAULT 1
        )
    """)

    # ── Students (attempt metadata) ────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            enrollment_no    TEXT    NOT NULL,
            quiz_id          INTEGER NOT NULL REFERENCES quizzes(id),
            attempted_at     DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Results ────────────────────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id),
            quiz_id     INTEGER NOT NULL REFERENCES quizzes(id),
            score       INTEGER NOT NULL DEFAULT 0,
            total_marks INTEGER NOT NULL DEFAULT 0,
            percentage  REAL    NOT NULL DEFAULT 0.0
        )
    """)

    conn.commit()
    conn.close()
    print("✅  Database initialised at", DB_PATH)


# ---------------------------------------------------------------------------
# Password utility
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of *password*."""
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Educator helpers
# ---------------------------------------------------------------------------

def register_educator(username: str, password: str) -> bool:
    """Insert a new educator; return False if username already taken."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO educators (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False          # username already exists


def verify_educator(username: str, password: str):
    """Return the educator row if credentials match, else None."""
    conn = get_connection()
    row  = conn.execute(
        "SELECT * FROM educators WHERE username=? AND password=?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# Quiz helpers
# ---------------------------------------------------------------------------

def create_quiz(educator_id: int, title: str, duration_mins: int, questions: list) -> str:
    """
    Persist a full quiz (metadata + questions) and return the quiz code.

    *questions* is a list of dicts:
      { text, option_a, option_b, option_c, option_d, correct, marks }
    """
    import random, string

    # Generate a unique 6-character alphanumeric code
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        conn = get_connection()
        exists = conn.execute(
            "SELECT id FROM quizzes WHERE quiz_code=?", (code,)
        ).fetchone()
        conn.close()
        if not exists:
            break

    total_marks = sum(int(q["marks"]) for q in questions)

    conn = get_connection()
    cur  = conn.cursor()

    cur.execute(
        "INSERT INTO quizzes (educator_id, title, quiz_code, total_marks, duration_mins) VALUES (?,?,?,?,?)",
        (educator_id, title, code, total_marks, duration_mins)
    )
    quiz_id = cur.lastrowid

    for q in questions:
        cur.execute("""
            INSERT INTO questions
              (quiz_id, question_text, option_a, option_b, option_c, option_d,
               correct_option, marks)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            quiz_id, q["text"],
            q["option_a"], q["option_b"], q["option_c"], q["option_d"],
            q["correct"].upper(), int(q["marks"])
        ))

    conn.commit()
    conn.close()
    return code


def get_quiz_by_code(code: str):
    """Return the quiz row for *code*, or None if not found."""
    conn = get_connection()
    row  = conn.execute(
        "SELECT * FROM quizzes WHERE quiz_code=?", (code.upper(),)
    ).fetchone()
    conn.close()
    return row


def get_questions(quiz_id: int) -> list:
    """Return all question rows for a quiz."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM questions WHERE quiz_id=?", (quiz_id,)
    ).fetchall()
    conn.close()
    return rows


def get_educator_quizzes(educator_id: int) -> list:
    """Return all quizzes created by an educator, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM quizzes WHERE educator_id=? ORDER BY created_at DESC",
        (educator_id,)
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Student / Result helpers
# ---------------------------------------------------------------------------

def save_result(name: str, enrollment_no: str, quiz_id: int, answers: dict) -> dict:
    """
    Score a student's submission and persist records to DB.

    *answers* maps question_id (str) → chosen option letter ('A'–'D').
    Returns a dict with score, total_marks, percentage, and per-question breakdown.
    """
    questions  = get_questions(quiz_id)
    score      = 0
    total      = 0
    breakdown  = []

    for q in questions:
        qid      = str(q["id"])
        chosen   = answers.get(qid, "").upper()
        correct  = q["correct_option"]
        marks    = q["marks"]
        total   += marks
        awarded  = marks if chosen == correct else 0
        score   += awarded
        breakdown.append({
            "question": q["question_text"],
            "chosen":   chosen,
            "correct":  correct,
            "marks":    marks,
            "awarded":  awarded
        })

    percentage = round((score / total * 100), 2) if total > 0 else 0.0

    conn = get_connection()
    cur  = conn.cursor()

    # Insert student record
    cur.execute(
        "INSERT INTO students (name, enrollment_no, quiz_id) VALUES (?,?,?)",
        (name, enrollment_no, quiz_id)
    )
    student_id = cur.lastrowid

    # Insert result
    cur.execute(
        "INSERT INTO results (student_id, quiz_id, score, total_marks, percentage) VALUES (?,?,?,?,?)",
        (student_id, quiz_id, score, total, percentage)
    )

    conn.commit()
    conn.close()

    return {
        "score":      score,
        "total":      total,
        "percentage": percentage,
        "breakdown":  breakdown
    }


def get_quiz_results(quiz_id: int) -> list:
    """Return all student results for a given quiz (for educator dashboard)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            s.name,
            s.enrollment_no,
            s.attempted_at,
            r.score,
            r.total_marks,
            r.percentage
        FROM results r
        JOIN students s ON s.id = r.student_id
        WHERE r.quiz_id = ?
        ORDER BY r.percentage DESC
    """, (quiz_id,)).fetchall()
    conn.close()
    return rows
