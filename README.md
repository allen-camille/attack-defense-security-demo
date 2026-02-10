# Attack & Defense Security Demo (Flask)

A small, hands-on demo that contrasts a **vulnerable** and a **secured** Flask application
to illustrate how common web vulnerabilities can be exploited and how proper defensive
controls mitigate them.

## What this repo shows
- A **vulnerable app** that demonstrates typical unsafe patterns (educational purpose)
- A **secure app** that implements safer patterns (input handling, output encoding, basic hardening)
- A simple message flow where behavior can be compared side-by-side

> ⚠️ **Safety note:**  
> The vulnerable app is intentionally insecure. Run locally only (e.g. `127.0.0.1`)  
> and never deploy it to the internet.

---

## Tech stack
- Python 3
- Flask
- SQLite (demo database)

---

## Project structure
- `vulnerable_app.py` – intentionally insecure version (attack surface)
- `secure_app.py` – hardened version (defensive controls)
- `requirements.txt` – dependencies
- `screenshots/` – visual comparison of attack vs defense

---

## Run locally (Windows / PowerShell)

### 1) Create & activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

2) Install dependencies

pip install -r requirements.txt

XSS demonstration (vulnerable app)

The vulnerable application does not properly validate or escape user input.
By submitting the following payload in the contact form, arbitrary JavaScript
is executed in the browser, allowing DOM manipulation.

Example payload (educational purpose)

<script>
document.body.innerHTML =
"<h1 style='color:red'>XSS-demo: sidan manipulerad</h1>" +
"<p>Detta är bara en visuell demonstration.</p>" +
document.body.innerHTML;
</script>

3) Run the vulnerable application

python vulnerable_app.py

Submit the payload in the application.
The browser executes the script and the page is visibly manipulated.

XSS mitigation (secure app)

The secure application demonstrates how the same input is handled safely by applying
output encoding / escaping and avoiding unsafe rendering patterns.

What changes in the secure version?

User input is treated as data, not executable code

Output is escaped before being rendered back to the page

The result: the payload is displayed as text instead of being executed by the browser

Run the secure application
python secure_app.py


Submit the same payload again.

Comparison

Vulnerable app:
Executes <script> input and allows client-side code execution.

Secure app:
Renders the same input as harmless text.

This illustrates a common real-world vulnerability where insufficient output encoding
can lead to client-side code execution, impacting user trust and application integrity.

Security relevance

This vulnerability corresponds to:

OWASP Top 10 – A03: Injection

Cross-Site Scripting (XSS)

XSS remains one of the most common web vulnerabilities and highlights the importance
of proper input handling and output encoding in modern web applications.
