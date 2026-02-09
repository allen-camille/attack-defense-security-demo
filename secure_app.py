# ============================
# secure_app.py
# Säker (fixad) version av labbapplikationen
# Syfte: Visa hur XSS och SQL-injection förhindras
# ============================

from flask import Flask, request, render_template_string, make_response
import sqlite3
import os
import time
import html       # Används för escaping av användarinmatning (XSS-skydd)
import logging    # Används för loggning av misstänkt beteende
import re         # Används för enkel mönsterdetektion (extra skyddslager)

# Skapar Flask-applikationen
app = Flask(__name__)

# --- Lab safety ---
# Applikationen körs ENDAST lokalt i VM
HOST = "127.0.0.1"
PORT = 5000

# Samma databasnamn som i vulnerable_app.py
# Detta gör före/efter-demo enklare
DB_FILE = "demo_portal.db"

# Grundläggande loggning (INFO-nivå räcker för labbdemo)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# ============================
# Bas-HTML (gemensamt skal)
# ============================
BASE_HTML = """
<!doctype html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <title>Folkhälsoportalen – Demo (SÄKER)</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 30px; max-width: 980px; }
    .banner { padding: 10px; background: #e9fff0; border: 1px solid #9ae6b4; border-radius: 8px; }
    .nav a { margin-right: 12px; }
    .box { padding: 14px; border: 1px solid #ddd; border-radius: 10px; margin-top: 14px; }
    input { padding: 8px; margin: 6px 0; width: 360px; }
    button { padding: 8px 14px; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 6px; }
    .ok { color: #0a6; }
    .warn { color: #b45309; }
    .err { color: #b91c1c; }
  </style>
</head>
<body>
  <div class="banner">
    <b>✅ Säker version (fixad)</b><br>
    SQL-frågor är parameteriserade och användarinput renderas säkert.
  </div>

  <div class="nav" style="margin-top:12px;">
    <a href="/">Start</a>
    <a href="/statistik">Statistik</a>
    <a href="/admin">Admin-sök</a>
    <a href="/kontakt">Kontakt</a>
    <a href="/health">Health</a>
  </div>

  <div class="box">
    {{ content|safe }}
  </div>
  <!--
    OBS:
    |safe används här endast på innehåll som vi själva kontrollerar.
    All användarinmatning escapadas FÖRE den når content.
  -->

  <p style="margin-top:18px; color:#666;">
    Version: <code>Secure v1.0</code> • Mode: <code>Lab / Demo</code> • DB: <code>{{ db_file }}</code>
  </p>
</body>
</html>
"""

# ============================
# Databas-helpers
# ============================
def get_db_conn():
    # timeout minskar risken för "database is locked" vid demo
    return sqlite3.connect(DB_FILE, timeout=5)

def init_db():
    # Idempotent init – kan köras flera gånger utan problem
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY,
            name TEXT,
            cases INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT
        )
    """)

    # Seed-data läggs bara in om tabellerna är tomma
    cur.execute("SELECT COUNT(*) FROM regions")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO regions (id, name, cases) VALUES (?, ?, ?)",
            [
                (1, "Stockholm", 123),
                (2, "Skåne", 98),
                (3, "Västra Götaland", 110),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users (id, username, role) VALUES (?, ?, ?)",
            [
                (1, "alice", "analyst"),
                (2, "bob", "admin"),
                (3, "charlie", "viewer"),
            ]
        )

    conn.commit()
    conn.close()

# Säkerställer att databasen finns före varje request
@app.before_request
def _ensure_db():
    init_db()

# ============================
# Extra (sekundärt) skydd: enkel mönsterdetektion
# OBS: Detta är INTE huvudskyddet
# ============================
SUSPICIOUS_RE = re.compile(
    r"(--|/\*|\*/|;|\bunion\b|\bselect\b|\bdrop\b|\bor\b\s+\d=\d)",
    re.IGNORECASE
)

def is_suspicious(value: str) -> bool:
    if not value:
        return False
    return bool(SUSPICIOUS_RE.search(value))

# ============================
# Säkerhetsheaders (defense-in-depth)
# ============================
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response

# ============================
# Health-endpoint (för demo)
# ============================
@app.get("/health")
def health():
    return {"status": "ok", "db_file": DB_FILE}, 200

# ============================
# Start-sida
# ============================
@app.get("/")
def home():
    content = """
    <h2>Start</h2>
    <p>Detta är den <b>fixade</b> versionen av labbportalen.</p>
    <ul>
      <li><b>SQLi</b> skyddas med <code>parameteriserade queries</code>.</li>
      <li><b>XSS</b> skyddas med <code>escaping</code> av användarinput.</li>
      <li>Extra: loggning och säkerhetsheaders.</li>
    </ul>
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Statistik – SQLi-skydd
# ============================
@app.route("/statistik", methods=["GET", "POST"])
def statistik():
    region_raw = request.form.get("region", "") if request.method == "POST" else ""
    region_safe = html.escape(region_raw, quote=True)

    result_html = ""
    if request.method == "POST":
        if is_suspicious(region_raw):
            logging.info("Suspicious input blocked on /statistik: %r", region_raw)
            result_html = "<p class='warn'><b>Input blockerad:</b> misstänkt mönster.</p>"
        else:
            try:
                conn = get_db_conn()
                cur = conn.cursor()

                # ✅ HUVUDFIX:
                # Parameteriserad query → ingen SQL-injection
                cur.execute(
                    "SELECT name, cases FROM regions WHERE name = ?",
                    (region_raw,)
                )
                rows = cur.fetchall()
                conn.close()

                if rows:
                    items = "".join(
                        [f"<li>{html.escape(r[0])}: <b>{r[1]}</b></li>" for r in rows]
                    )
                    result_html = f"<ul>{items}</ul>"
                else:
                    result_html = "<p><b>Inga resultat.</b></p>"

            except Exception:
                logging.exception("Database error in /statistik")
                result_html = "<p class='err'>Tekniskt fel.</p>"

    content = f"""
    <h2>Statistik</h2>
    <form method="post">
      <input name="region" value="{region_safe}">
      <button>Sök</button>
    </form>
    <hr>
    {result_html}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Admin – SQLi-skydd
# ============================
@app.route("/admin", methods=["GET", "POST"])
def admin_search():
    username_raw = request.form.get("username", "") if request.method == "POST" else ""
    username_safe = html.escape(username_raw, quote=True)
    out = ""

    if request.method == "POST":
        if is_suspicious(username_raw):
            logging.info("Suspicious input blocked on /admin: %r", username_raw)
            out = "<p class='warn'>Misstänkt input blockerad.</p>"
        else:
            try:
                conn = get_db_conn()
                cur = conn.cursor()

                # ✅ Parameteriserad query
                cur.execute(
                    "SELECT id, username, role FROM users WHERE username = ?",
                    (username_raw,)
                )
                rows = cur.fetchall()
                conn.close()

                if rows:
                    out = "<ul>" + "".join(
                        [f"<li>{r[1]} ({r[2]})</li>" for r in rows]
                    ) + "</ul>"
                else:
                    out = "<p>Inga träffar.</p>"

            except Exception:
                logging.exception("Database error in /admin")
                out = "<p class='err'>Tekniskt fel.</p>"

    content = f"""
    <h2>Admin-sök</h2>
    <form method="post">
      <input name="username" value="{username_safe}">
      <button>Sök</button>
    </form>
    <hr>
    {out}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Kontakt – XSS-skydd
# ============================
@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    message_raw = request.form.get("message", "") if request.method == "POST" else ""
    # ✅ HUVUDFIX MOT XSS:
    # Användarinmatning escapadas innan rendering
    message_safe = html.escape(message_raw, quote=True)

    rendered = ""
    if request.method == "POST":
        rendered = f"""
        <p class="ok"><b>Tack för ditt meddelande!</b></p>
        <div>{message_safe}</div>
        """

    content = f"""
    <h2>Kontakt</h2>
    <form method="post">
      <input name="message" value="{message_safe}">
      <button>Skicka</button>
    </form>
    <hr>
    {rendered}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Startar applikationen
# ============================
if __name__ == "__main__":
    print("[INFO] Starting secure demo app (localhost only)")
    print(f"[INFO] URL: http://{HOST}:{PORT}")
    time.sleep(0.3)
    app.run(host=HOST, port=PORT, debug=False)
