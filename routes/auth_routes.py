"""
================================================================================
  routes/auth_routes.py  –  Login / Logout / Registration
================================================================================
  GET  /              → redirect to /login
  GET  /login         → render login page
  POST /login         → authenticate educator or start student flow
  POST /register      → register a new educator account
  GET  /logout        → clear session, redirect to /login
================================================================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from database.db import verify_educator, register_educator

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json()
    role = data.get("role")           # "educator" or "student"

    if role == "educator":
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        educator = verify_educator(username, password)
        if not educator:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

        # Store educator info in session
        session["educator_id"]   = educator["id"]
        session["educator_name"] = educator["username"]
        return jsonify({"success": True, "redirect": "/educator/dashboard"})

    elif role == "student":
        # Students don't need an account; they jump straight to quiz access
        return jsonify({"success": True, "redirect": "/student/join"})

    return jsonify({"success": False, "message": "Unknown role"}), 400


# ---------------------------------------------------------------------------
# Register (educator only)
# ---------------------------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    ok = register_educator(username, password)
    if not ok:
        return jsonify({"success": False, "message": "Username already taken"}), 409

    return jsonify({"success": True, "message": "Account created — please log in"})


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
