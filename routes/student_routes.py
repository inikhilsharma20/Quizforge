"""
================================================================================
  routes/student_routes.py  –  Student-facing endpoints
================================================================================
  GET  /student/join              → enter quiz code + personal details
  GET  /student/quiz/<code>       → display questions
  POST /student/submit            → score & store answers, redirect to result
  GET  /student/result            → show score breakdown (from session)
================================================================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database.db import get_quiz_by_code, get_questions, save_result

student_bp = Blueprint("student", __name__, url_prefix="/student")


# ---------------------------------------------------------------------------
# Join page  (enter quiz code + name)
# ---------------------------------------------------------------------------

@student_bp.route("/join", methods=["GET"])
def join():
    return render_template("student_join.html")


# ---------------------------------------------------------------------------
# Validate quiz code (AJAX) + store student info in session
# ---------------------------------------------------------------------------

@student_bp.route("/validate", methods=["POST"])
def validate_quiz():
    """
    Expects JSON: { "quiz_code": "AB12CD", "name": "Alice", "enrollment": "2021CS001" }
    Returns { "success": true } or { "success": false, "message": "..." }
    """
    data    = request.get_json()
    code    = data.get("quiz_code", "").strip().upper()
    name    = data.get("name", "").strip()
    enroll  = data.get("enrollment", "").strip()

    if not code or not name or not enroll:
        return jsonify({"success": False, "message": "All fields are required"}), 400

    quiz = get_quiz_by_code(code)
    if not quiz:
        return jsonify({"success": False, "message": "Invalid quiz code"}), 404

    # Store in session so the quiz page can use them
    session["student_name"]    = name
    session["student_enroll"]  = enroll
    session["current_quiz_id"] = quiz["id"]
    session["current_quiz_code"] = code

    return jsonify({"success": True, "redirect": f"/student/quiz/{code}"})


# ---------------------------------------------------------------------------
# Attempt quiz
# ---------------------------------------------------------------------------

@student_bp.route("/quiz/<code>")
def attempt_quiz(code):
    quiz = get_quiz_by_code(code)
    if not quiz:
        return redirect(url_for("student.join"))

    # Ensure student registered for this quiz
    if session.get("current_quiz_id") != quiz["id"]:
        return redirect(url_for("student.join"))

    questions = get_questions(quiz["id"])
    return render_template(
        "attempt_quiz.html",
        quiz=dict(quiz),
        questions=[dict(q) for q in questions],
        student_name=session.get("student_name", ""),
        student_enroll=session.get("student_enroll", "")
    )


# ---------------------------------------------------------------------------
# Submit answers
# ---------------------------------------------------------------------------

@student_bp.route("/submit", methods=["POST"])
def submit():
    """
    Expects JSON: { "answers": { "12": "A", "13": "C", ... } }
    Scores the quiz, saves to DB, stores result in session, redirects to /result.
    """
    data    = request.get_json()
    answers = data.get("answers", {})

    quiz_id = session.get("current_quiz_id")
    name    = session.get("student_name")
    enroll  = session.get("student_enroll")

    if not quiz_id or not name or not enroll:
        return jsonify({"success": False, "message": "Session expired, please rejoin"}), 400

    result = save_result(name, enroll, quiz_id, answers)

    # Store result in session for the result page
    session["last_result"] = result

    return jsonify({"success": True, "redirect": "/student/result"})


# ---------------------------------------------------------------------------
# Result page
# ---------------------------------------------------------------------------

@student_bp.route("/result")
def result():
    result = session.get("last_result")
    if not result:
        return redirect(url_for("student.join"))

    return render_template(
        "result.html",
        result=result,
        student_name=session.get("student_name", ""),
        student_enroll=session.get("student_enroll", "")
    )
