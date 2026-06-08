#!/usr/bin/env python3
"""
sqli-login-triage.py — triage vuln-lab auth logs for SQL injection login bypass.

Mirrors the Sigma rules in ../02-detection-and-playbook/ so the script and the
deployed detection rules share one logic:

  GATE (mirrors Sigma 'selection'):
      event == "login_attempt"  AND  username contains "'"   <- the SQLi indicator
  Then the result field decides severity:
      result == "failed"   -> medium    (attempt, did not break in)  [sqli-login-attempt]
      result == "success"  -> critical  (auth bypass succeeded)      [sqli-login-success]

A username WITHOUT "'" never trips the gate, so normal logins (alice/bob) are
not flagged regardless of success/failure. The single quote is the gate;
result is only the discriminator after a SQLi attempt is confirmed.

Known limitation (documented, mirrors the Sigma rule's falsepositives):
  Legitimate usernames containing an apostrophe (e.g. O'Brien) also trip the
  gate. The rule flags-and-documents rather than auto-excluding; the structural
  fix is to block "'" at registration.
"""

import argparse
import json
import sys
from pathlib import Path

SQLI_INDICATOR = "'"

# result -> (severity, source Sigma rule) — keeps each finding traceable back
# to the exact deployed rule, while the shared gate is evaluated only once.
RULES = {
    "failed":  {"level": "medium",   "rule": "sqli-login-attempt",
                "rule_id": "7d25465e-5085-401e-8781-cf2451b41be0"},
    "success": {"level": "critical", "rule": "sqli-login-success",
                "rule_id": "ec284efe-d72b-436c-8cf8-61e238e66d68"},
}


def triage_line(entry):
    """Return a finding dict if the entry trips the SQLi gate, else None."""
    # GATE — both conditions must hold (mirrors Sigma 'condition: selection')
    if entry.get("event") != "login_attempt":
        return None
    if SQLI_INDICATOR not in entry.get("username", ""):
        return None

    # SQLi indicator confirmed -> severity comes from the login result
    rule = RULES.get(entry.get("result"))
    if rule is None:
        return None  # unknown/missing result -> don't guess a severity

    return {
        "timestamp": entry.get("timestamp"),
        "src_ip": entry.get("src_ip"),
        "username": entry.get("username"),
        "result": entry.get("result"),
        **rule,
    }


def parse_log(path):
    """Yield findings from a JSON-lines auth log, skipping malformed lines."""
    findings = []
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            print(f"[!] Skipping malformed JSON on line {n}", file=sys.stderr)
            continue
        finding = triage_line(entry)
        if finding:
            findings.append(finding)
    return findings


def report(path, findings):
    critical = [f for f in findings if f["level"] == "critical"]
    medium = [f for f in findings if f["level"] == "medium"]

    print("=== SQLi Login Triage ===")
    print(f"Log: {path}")
    print(f"Flagged: {len(findings)}  "
          f"(critical: {len(critical)}, medium: {len(medium)})\n")

    # critical first
    for f in sorted(findings, key=lambda x: x["level"] != "critical"):
        print(f"[{f['level'].upper():>8}] {f['timestamp']}  {f['src_ip']:<15} "
              f"username={f['username']!r}  result={f['result']}  "
              f"(rule: {f['rule']})")

    if critical:
        print(f"\n[CONFIRMED BREACH] {len(critical)} successful SQLi auth "
              f"bypass — escalate per 02-detection-and-playbook/incident-playbook.md")

    return critical


def main():
    ap = argparse.ArgumentParser(
        description="Triage vuln-lab auth logs for SQLi login-bypass attempts.")
    ap.add_argument(
        "logfile", nargs="?",
        default="02-detection-and-playbook/sample-logs/login-attack.log",
        help="Path to the JSON-lines auth log (run from repo root, "
             "or pass an explicit path)")
    args = ap.parse_args()

    path = Path(args.logfile)
    if not path.exists():
        print(f"[!] Log file not found: {path}", file=sys.stderr)
        sys.exit(2)

    findings = parse_log(path)
    critical = report(path, findings)

    # non-zero exit when a confirmed breach is present — lets this run as a
    # gate in a CI/pipeline (optional; remove the exit if not wanted).
    sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main()