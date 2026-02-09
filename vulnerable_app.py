# ============================
# vulnerable_app.py
# Avsiktligt sårbar demoapplikation
# Syfte: Visa XSS och SQL-injection i labbmiljö
# ============================

from flask import Flask, request, render_template_string
import sqlite3
import os
import time

# Skapar Flask-applikationen
app = Flask(__name__)

# --- Lab safety ---
# Applikationen binds ENDAST till localhost
# Detta är viktigt eftersom applikationen är avsiktligt sårbar
HOST = "127.0.0.1"
PORT = 5000

# SQLite-databas som används i labben
DB_FILE = "demo_portal.db"

# ============================
# Bas-HTML för hela applikationen
# ============================
BASE_HTML = """
<!doctype html>
<html lang="sv">
<head>
  <meta charset="utf-8">
  <title>Folkhälsoportalen – Demo (SÅRBAR)</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 30px; max-width: 980px; }
    .banner { padding: 10px; background: #ffe8e8; border: 1px solid #ffb3b3; border-radius: 8px; }
    .nav a { margin-right: 12px; }
    .box { padding: 14px; border: 1px solid #ddd; border-radius: 10px; margin-top: 14px; }
    input { padding: 8px; margin: 6px 0; width: 360px; }
    button { padding: 8px 14px; }
    code { background: #f5f5f5; padding: 2px 6px; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="banner">
    <b>⚠️ Avsiktligt sårbar labbapp</b><br>
    Kör endast i isolerad VM. Exponera inte porten utåt.
  </div>

  <div class="nav" style="margin-top:12px;">
    <a href="/">Start</a>
    <a href="/statistik">Statistik</a>
    <a href="/admin">Admin-sök</a>
    <a href="/kontakt">Kontakt</a>
  </div>

  <div class="box">
    {{ content|safe }}
  </div>
  <!--
    ⚠️ KRITISK DETALJ:
    Jinja-filtret |safe innebär att innehållet INTE escapadas.
    All HTML och JavaScript som finns i variabeln 'content'
    kommer att renderas och exekveras av webbläsaren.
    Detta är en direkt orsak till XSS-sårbarheten.
  -->

  <p style="margin-top:18px; color:#666;">
    Version: <code>Vulnerable v1.0</code> • Mode: <code>Lab / Demo</code> • Environment: <code>Local VM</code>
 • DB: <code>{{ db_file }}</code>
  </p>
</body>
</html>
"""

# ============================
# Databasinitiering (endast för labb)
# ============================
def init_db():
    # Om databasen redan finns, gör inget
    if os.path.exists(DB_FILE):
        return

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Skapar tabeller
    cur.execute("CREATE TABLE regions (id INTEGER PRIMARY KEY, name TEXT, cases INTEGER)")
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT)")

    # Lägger in demo-data
    cur.executemany(
        "INSERT INTO regions (id, name, cases) VALUES (?, ?, ?)",
        [
            (1, "Stockholm", 123),
            (2, "Skåne", 98),
            (3, "Västra Götaland", 110),
        ]
    )

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

# Säkerställer att databasen finns innan varje request
@app.before_request
def _ensure_db():
    init_db()

# ============================
# Start-sida
# ============================
@app.get("/")
def home():
    content = """
    <h2>Start</h2>
    <p>Detta är en labbportal för att demonstrera sårbarheter och åtgärder.</p>
    <ul>
      <li><b>SQLi-risk</b> i <code>/statistik</code> och <code>/admin</code>.</li>
      <li><b>XSS-risk</b> i <code>/kontakt</code>.</li>
    </ul>
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Statistik – SQL Injection (sekundär sårbarhet)
# ============================
@app.route("/statistik", methods=["GET", "POST"])
def statistik():
    region = request.form.get("region", "") if request.method == "POST" else ""
    result_html = ""

    if request.method == "POST":
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()

            # ❌ AVSIKTLIGT SÅRBART:
            # Användarinmatning sätts direkt in i SQL-strängen
            query = f"SELECT name, cases FROM regions WHERE name = '{region}'"
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()

            if rows:
                items = "".join([f"<li>{r[0]}: <b>{r[1]}</b> rapporterade fall</li>" for r in rows])
                result_html = f"<p><b>Resultat:</b></p><ul>{items}</ul>"
            else:
                result_html = "<p><b>Inga resultat.</b></p>"

        except Exception as e:
            # ❌ Informationsläckage vid fel
            result_html = f"<p style='color:red;'><b>Fel:</b> {e}</p>"

    content = f"""
    <h2>Statistik</h2>
    <p>Sök statistik per region (demo).</p>
    <form method="post">
      <label>Region:</label><br>
      <input name="region" placeholder="t.ex. Stockholm" value="{region}">
      <br><button type="submit">Sök</button>
    </form>
    <hr>
    {result_html}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Admin-sök – SQL Injection
# ============================
@app.route("/admin", methods=["GET", "POST"])
def admin_search():
    username = request.form.get("username", "") if request.method == "POST" else ""
    out = ""

    if request.method == "POST":
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()

            # ❌ AVSIKTLIGT SÅRBART:
            query = f"SELECT id, username, role FROM users WHERE username = '{username}'"
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()

            if rows:
                out = "<p><b>Träffar:</b></p><ul>" + "".join(
                    [f"<li>ID {r[0]} – {r[1]} ({r[2]})</li>" for r in rows]
                ) + "</ul>"
            else:
                out = "<p><b>Inga träffar.</b></p>"

        except Exception as e:
            out = f"<p style='color:red;'><b>Fel:</b> {e}</p>"

    content = f"""
    <h2>Admin-sök</h2>
    <p>Intern sökfunktion (demo).</p>
    <form method="post">
      <label>Användarnamn:</label><br>
      <input name="username" placeholder="t.ex. alice" value="{username}">
      <br><button type="submit">Sök</button>
    </form>
    <hr>
    {out}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Kontakt – HUVUDSÅRBARHETEN (XSS)
# ============================
@app.route("/kontakt", methods=["GET", "POST"])
def kontakt():
    message = request.form.get("message", "") if request.method == "POST" else ""
    rendered = ""

    if request.method == "POST":
        # ❌ KRITISK XSS-SÅRBARHET:
        # Användarinmatning renderas direkt i HTML
        # Ingen escaping eller sanering sker
        rendered = f"""
        <p><b>Tack för ditt meddelande!</b></p>
        <p>Du skrev:</p>
        <div style="padding:10px;border:1px dashed #bbb;border-radius:8px;">
          {message}
        </div>
        """

    content = f"""
    <h2>Kontakt</h2>
    <p>Skicka ett meddelande (demo).</p>
    <form method="post">
      <label>Meddelande:</label><br>
      <input name="message" placeholder="Skriv något..." value="{message}">
      <br><button type="submit">Skicka</button>
    </form>
    <hr>
    {rendered}
    """
    return render_template_string(BASE_HTML, content=content, db_file=DB_FILE)

# ============================
# Startar applikationen
# ============================
if __name__ == "__main__":
    print("[INFO] Starting vulnerable demo app (localhost only)")
    print(f"[INFO] URL: http://{HOST}:{PORT}")
    time.sleep(0.3)
    app.run(host=HOST, port=PORT, debug=False)
