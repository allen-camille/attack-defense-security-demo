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
- `demo_portal.db` – demo database

---

## Run locally (Windows / PowerShell)

----


---

## XSS demonstration (vulnerable app)

The vulnerable application does not properly validate or escape user input.
By submitting the following payload in the contact form, arbitrary JavaScript
is executed in the browser, allowing DOM manipulation.

**Example payload (educational purpose):**

```html
<script>
document.body.innerHTML =
"<h1 style='color:red'>XSS-demo: sidan manipulerad</h1>" +
"<p>Detta är bara en visuell demonstration.</p>" +
document.body.innerHTML;
</script>
-----


### 1) Create & activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

### 2) Install dependencies
```powershell
pip install -r requirements.txt

```markdown
### 3) Run the vulnerable application
```powershell
python vulnerable_app.py


