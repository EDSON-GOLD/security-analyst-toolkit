# Security Analyst Toolkit

> A web application security portfolio built on one idea: a real analyst doesn't stop at finding a vulnerability. Each section traces a flaw from **root cause to a structural fix a developer can act on** — across the find, the detection, and the report.

Most security work gets siloed: the pentester finds a bug and throws it over the wall, the SOC analyst forwards an alert, the systems owner knows something is wrong but not how to fix it. This repository shows the opposite — one person following a vulnerability through the entire lifecycle, and making the output usable by the developers who have to fix it.

## How the sections connect

These aren't separate exercises. They follow **one deliberately vulnerable application** through the security lifecycle:

| Section | What it is | What it demonstrates |
|---------|-----------|----------------------|
| **01 — Vulnerable Lab** | A Flask + SQLite app I built with SQL Injection, Stored XSS, IDOR, and Insecure Password Reset, containerized with Docker | Understanding each flaw well enough to *create* it, not just exploit it — the offense and code-review side |
| **02 — Detection & Playbook** | Sigma detection rules + an incident-response playbook for attacks against the lab | The defender's view — you can't detect what you don't log |
| **03 — Automation** | A Python script that triages the lab's auth logs and flags SQLi login-bypass, reusing the same logic as the Section 02 Sigma rules | Turning detection logic into automation — the triage / scale side |
| **04 — Pentest Report** | A professional report on the lab's findings, with root-cause analysis and developer-actionable remediation | Communicating findings so a developer can act on them — the handoff most reports get wrong |

The same `id` parameter that exposes data through IDOR in Section 01 is also the SQL injection sink — and because passwords are stored in plaintext, that chain ends in full account takeover. The same IDOR also feeds a **second** takeover path through an insecure password-reset flow, which still works even after the SQL injection is fixed. Tracing the chains end-to-end (01), detecting them (02), and reporting them for a structural fix (04) is the point.

## Quick start (Section 01 lab)

```bash
cd 01-vulnerable-lab
docker-compose up --build
```

Then open **http://localhost:5000** and navigate Register / Login / Profile / Review / Forgot Password.

> ⚠️ This lab is **intentionally vulnerable** and for educational / portfolio use only. Do not deploy it to any internet-facing environment.

## Tech & skills

- **App / language:** Python, Flask, Jinja2
- **Data:** SQLite
- **Infrastructure:** Docker, docker-compose
- **Detection:** Sigma rules, JSON-structured application logging
- **Testing:** Burp Suite, Nmap
- **Standards:** OWASP Top 10 (A01, A02, A03, A04, A05, A07)