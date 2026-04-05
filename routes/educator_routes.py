"""
================================================================================
  routes/educator_routes.py  –  Educator-facing endpoints
================================================================================
  GET  /educator/dashboard          → list all quizzes + results
  GET  /educator/create             → quiz creation form
  POST /educator/create             → save quiz, return generated code
  GET  /educator/quiz/<quiz_id>     → results for a specific quiz
================================================================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database.db import (
    create_quiz, get_educator_quizzes, get_quiz_results, get_questions, get_quiz_by_code
)

educator_bp = Blueprint("educator", __name__, url_prefix="/educator")


# ---------------------------------------------------------------------------
# Guard: require educator session
# ---------------------------------------------------------------------------

def require_educator():
    """Return None if logged in, else a redirect response."""
    if "educator_id" not in session:
        return redirect(url_for("auth.login"))
    return None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@educator_bp.route("/dashboard")
def dashboard():
    guard = require_educator()
    if guard:
        return guard

    quizzes = get_educator_quizzes(session["educator_id"])
    # Attach result counts to each quiz object (convert Row → dict first)
    quizzes_data = []
    for q in quizzes:
        results  = get_quiz_results(q["id"])
        quizzes_data.append({
            "id":            q["id"],
            "title":         q["title"],
            "quiz_code":     q["quiz_code"],
            "total_marks":   q["total_marks"],
            "duration_mins": q["duration_mins"],
            "created_at":    q["created_at"],
            "attempt_count": len(results)
        })

    return render_template(
        "educator_dashboard.html",
        educator_name=session["educator_name"],
        quizzes=quizzes_data
    )


# ---------------------------------------------------------------------------
# Create Quiz
# ---------------------------------------------------------------------------

@educator_bp.route("/create", methods=["GET"])
def create_quiz_page():
    guard = require_educator()
    if guard:
        return guard
    return render_template("create_quiz.html")


@educator_bp.route("/create", methods=["POST"])
def create_quiz_api():
    """
    Accepts JSON body:
    {
      "title": "Maths Quiz",
      "questions": [
        {
          "text": "What is 2+2?",
          "option_a": "3", "option_b": "4", "option_c": "5", "option_d": "6",
          "correct": "B",
          "marks": 2
        }, ...
      ]
    }
    Returns { "success": true, "quiz_code": "AB12CD" }
    """
    guard = require_educator()
    if guard:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data      = request.get_json()
    title     = data.get("title", "Untitled Quiz").strip()
    duration  = int(data.get("duration", 30) or 30)
    questions = data.get("questions", [])

    if duration < 1 or duration > 180:
        return jsonify({"success": False, "message": "Duration must be between 1 and 180 minutes."}), 400

    if not questions:
        return jsonify({"success": False, "message": "At least one question required"}), 400

    quiz_code = create_quiz(session["educator_id"], title, duration, questions)
    return jsonify({"success": True, "quiz_code": quiz_code})


# ---------------------------------------------------------------------------
# Quiz Results (for educator to review)
# ---------------------------------------------------------------------------

@educator_bp.route("/quiz/<int:quiz_id>")
def quiz_results(quiz_id):
    guard = require_educator()
    if guard:
        return guard

    # Fetch results rows
    rows      = get_quiz_results(quiz_id)
    questions = get_questions(quiz_id)

    # Build quiz title from first question's quiz_id lookup
    conn_results = [dict(r) for r in rows]

    # Retrieve quiz meta
    from database.db import get_connection
    conn = get_connection()
    quiz = conn.execute("SELECT * FROM quizzes WHERE id=?", (quiz_id,)).fetchone()
    conn.close()

    if not quiz or quiz["educator_id"] != session["educator_id"]:
        return redirect(url_for("educator.dashboard"))

    return render_template(
        "quiz_results.html",
        quiz=dict(quiz),
        results=conn_results,
        questions=[dict(q) for q in questions]
    )
