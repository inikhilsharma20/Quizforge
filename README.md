# ⬡ QuizForge — Online Quiz System

A full-stack quiz platform built with **Flask + SQLite** and a dark-themed, mobile-responsive frontend.

---

## 📂 Project Structure

```
quiz_system/
├── app.py                     # Flask entry point / app factory
├── requirements.txt
│
├── database/
│   ├── __init__.py
│   └── db.py                  # Schema, all DB helpers, password utils
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py         # /login, /logout, /register
│   ├── educator_routes.py     # /educator/*
│   └── student_routes.py      # /student/*
│
├── templates/
│   ├── base.html              # Shared head / font imports
│   ├── login.html             # Role selector + educator login
│   ├── educator_dashboard.html
│   ├── create_quiz.html
│   ├── quiz_results.html      # Per-quiz results for educator
│   ├── student_join.html      # Enter code + name
│   ├── attempt_quiz.html      # Live quiz with timer
│   └── result.html            # Animated score breakdown
│
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## 🗄️ Database Schema

```
educators   id | username | password (SHA-256) | created_at
quizzes     id | educator_id → educators | title | quiz_code | total_marks | created_at
questions   id | quiz_id → quizzes | question_text | option_a-d | correct_option | marks
students    id | name | enrollment_no | quiz_id → quizzes | attempted_at
results     id | student_id → students | quiz_id → quizzes | score | total_marks | percentage
```

---

## 🔄 Application Flow

```
Browser
  │
  ├─ GET /  ──────────────────────────────────────── redirect → /login
  │
  ├─ /login (role selector)
  │     ├─ Educator  → POST /login  → session set → /educator/dashboard
  │     └─ Student   → no auth     →               /student/join
  │
  ├─ /educator/dashboard  (requires session)
  │     └─ shows all quizzes + attempt counts
  │
  ├─ /educator/create  (GET → form, POST → saves quiz, returns code)
  │
  ├─ /educator/quiz/<id>  (results table + question breakdown)
  │
  ├─ /student/join  (name + enroll + quiz code form)
  │     └─ POST /student/validate  → stores to session → /student/quiz/<code>
  │
  ├─ /student/quiz/<code>  (attempt page with 30-min timer)
  │     └─ POST /student/submit  → save_result() → /student/result
  │
  └─ /student/result  (animated ring chart + per-question breakdown)
```

---

## 🚀 Setup & Run

```bash
# 1. Clone / copy the quiz_system folder, then:
cd quiz_system

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The SQLite database file (`database/quiz.db`) is created automatically on first run.

---

## 🔑 Features At a Glance

| Feature | Detail |
|---------|--------|
| Educator Auth | SHA-256 hashed passwords, Flask sessions |
| Quiz Codes | Random 6-char alphanumeric, guaranteed unique |
| Timed Quiz | 30-minute countdown, auto-submits on expiry |
| Live Progress | Progress bar + dot tracker as student answers |
| Instant Results | Animated percentage ring + per-question breakdown |
| Educator Dashboard | Attempt counts, class average, grade distribution |
| Responsive | Works on mobile (sidebar hidden, stacked layout) |

---

## 🔒 Security Notes (for production)

- Replace `app.secret_key` with a strong random value via env variable
- Add CSRF protection (Flask-WTF)
- Switch to bcrypt/argon2 for password hashing
- Use PostgreSQL or MySQL instead of SQLite
- Add rate limiting on `/login` and `/student/validate`
