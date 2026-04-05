"""
================================================================================
  Online Quiz System - Flask Backend (app.py)
  Main entry point: registers blueprints, initialises DB, and runs the server.
================================================================================
"""

from flask import Flask
from database.db import init_db
from routes.auth_routes   import auth_bp
from routes.educator_routes import educator_bp
from routes.student_routes  import student_bp
import os

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Secret key for session management (change in production!)
    app.secret_key = os.environ.get("SECRET_KEY", "quiz-secret-key-2024")

    # ── Initialise SQLite database ──────────────────────────────────────────
    init_db()

    # ── Register blueprints (route groups) ─────────────────────────────────
    app.register_blueprint(auth_bp)          # /login, /logout
    app.register_blueprint(educator_bp)      # /educator/*
    app.register_blueprint(student_bp)       # /student/*

    return app


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = create_app()
    print("🚀  Quiz System running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
