/**
 * main.js  –  Shared frontend utilities for QuizForge
 * -------------------------------------------------------
 * Provides:
 *   post(url, data)        – JSON POST helper, returns Response
 *   showError(el, msg)     – show an error message element
 *   showSuccess(el, msg)   – show a success message element
 *
 * All pages include this file via the base template.
 */

/* ── JSON POST helper ───────────────────────────────────────── */
/**
 * Send a JSON POST request and return the raw Response.
 * Usage:
 *   const res  = await post("/login", { username, password });
 *   const data = await res.json();
 */
async function post(url, data) {
  return fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(data)
  });
}

/* ── Error / success message helpers ───────────────────────── */
function showError(el, msg) {
  el.textContent = msg;
  el.classList.remove("hidden");
}

function showSuccess(el, msg) {
  el.textContent = msg;
  el.classList.remove("hidden");
}

/* ── Auto-uppercase quiz-code input fields ──────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[maxlength='6']").forEach(el => {
    el.addEventListener("input", () => {
      el.value = el.value.toUpperCase();
    });
  });
});
