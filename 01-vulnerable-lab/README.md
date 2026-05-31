# Vulnerable Lab — Security Analyst Toolkit (Section 01)

A deliberately vulnerable web application built with **Flask + SQLite**, containerized with **Docker**. It implements three OWASP-relevant vulnerabilities — **SQL Injection, Stored XSS, and IDOR** — to demonstrate hands-on understanding of how each flaw arises, what an attacker can do with it, and how to fix it properly.

## Why build it from scratch (instead of DVWA / Juice Shop)

DVWA and OWASP Juice Shop are excellent references, and I studied them. But I built my own lab to understand each vulnerability deeply enough to *create* it — not just exploit it. Being able to write both the vulnerable code and the secure fix is the level of understanding that carries over to real code review.

### Tech choices

- **Flask** over Django — lightweight and transparent in structure, which suits deliberately introducing vulnerabilities. Django ships with security features I'd otherwise have to turn off.
- **SQLite** over MySQL/PostgreSQL — no separate DB server to set up; anyone can `git clone` and run it immediately. In production I'd use PostgreSQL or MySQL.

## How to run

```bash
docker-compose up --build
```

Then open **http://localhost:5000** and navigate between Register / Login / Profile / Review.

---

## Vulnerabilities

### 1. SQL Injection — Login form (`/login`)

- **Root cause** — The SQL query is built by string concatenation with user input directly. This lets the input escape the "data" context and be parsed as SQL syntax (code) by the database engine.
- **Impact** — Authentication bypass via a payload like `' OR 1=1--`. SQLi impact is broader than login bypass: it ranges up to full database exfiltration (UNION-based) and data tampering.
- **Remediation**
  1. **Parameterized queries / prepared statements (primary fix)** — use `?` placeholders so the driver sends query structure and values separately; input is treated strictly as data and can never execute as SQL.
  2. **Least privilege on the DB account** — restrict the app's DB user to only what it needs, limiting damage if exploited.
  3. **Input validation (defense-in-depth only)** — helpful as an extra layer, but never the primary defense; blocklisting keywords is bypassable via encoding, case changes, and comments.

### 2. Stored XSS — Review page (`/review`)

- **Root cause** — User input is rendered back into the page **without output encoding**, so the browser interprets it as HTML/JS instead of plain text. In this app it's caused by the `| safe` filter in Jinja2, which disables the auto-escaping the framework provides by default. *XSS is fundamentally an output problem, not a storage problem.*
- **Impact** — Because the payload is persisted in the database, it executes for **every** visitor who views the page (unlike Reflected XSS, which targets a single victim). Enables session cookie theft, actions performed on behalf of victims, and redirects to phishing pages.
- **Remediation**
  1. **Output encoding (primary fix)** — encode special characters on output (`<` → `&lt;`) so they display as text. Remove `| safe` and let Jinja2 auto-escape.
  2. **Safe DOM methods (client-side)** — use `textContent` instead of `innerHTML` so values can only be inserted as text, never rendered as HTML.
  3. **Content Security Policy (CSP) header** — tell the browser which sources are allowed to run JavaScript, restricting execution to trusted origins.
  4. **`HttpOnly` flag on session cookies (defense-in-depth)** — prevents JavaScript from reading `document.cookie`, limiting damage if an XSS slips through.

### 3. IDOR — Profile page (`/profile?id=`)

- **Root cause** — The server trusts the `id` supplied by the client without checking whether the requester is authorized to view that resource.
- **Impact** — Changing `?id=1` → `?id=2` exposes any user's data. In this app it's worse: no login is required at all — both **authentication** and **authorization** checks are missing.
- **Remediation**
  1. **Server-side authorization check (primary fix)** — verify that the current session owns or is permitted to access the requested resource; never trust the client-supplied id.
  2. **Authentication check** — require login before the profile page is reachable.
  3. **Defense-in-depth** — unguessable references (UUID) or an indirect reference map reduce enumeration risk, but are **not** a fix on their own without the authorization check.

---

## Lessons / Challenges

- **Two vulnerabilities collided.** Testing a Stored XSS payload `<script>alert('XSS')</script>` threw a SQL error — the single quote inside `alert('XSS')` closed the SQL `INSERT` string early. Both flaws share the same root cause (unhandled user input), so they fought over breaking the SQL structure. Workaround for testing: double quotes.
- **`venv/` leaked into git.** Added `venv/` and `*.db` to `.gitignore`, then used `git rm --cached` to remove what was already pushed.
- **Docker file-sync confusion.** Without a volume mount, editing template files on the host doesn't update a running container — the image is a build-time snapshot. Rebuilding with `docker-compose up --build` solved it. This surfaced the tradeoff between dev convenience (volume mount) and production reproducibility (`COPY` into the image).
- **A recurring pattern when fixing injection / access-control flaws.** The real fix is structural — parameterized queries, server-side authorization checks — not blocklisting "bad" input. Input filtering loses to creative attackers and belongs in the supplementary layer, never the primary defense.

---

## ⚠️ Disclaimer

This application is **intentionally vulnerable** and built for educational and portfolio purposes only. **Do not deploy it to any production or internet-facing environment.** By design it lacks authentication, secure input handling, HTTPS, secrets management, and other production essentials.