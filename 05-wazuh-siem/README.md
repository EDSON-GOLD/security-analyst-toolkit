# 05 — Wazuh SIEM: SQLi Detection (Native Rule)

Real-time detection of the SQL injection login attack from the lab (Section 01), running as a native Wazuh rule on a single-node Wazuh 4.9.0 stack.


## Where this fits — one logic, three forms
The same detection logic is expressed three times across this toolkit:

| Form | Location | Runs where | Use case |
|------|----------|-----------|----------|
| Sigma rule | `02-detection-and-playbook` | SIEM with a Sigma backend (Splunk/Elastic) | portable, vendor-neutral spec |
| Python parser | `03-automation-scripts` | anywhere with Python | no SIEM / IR / historical logs |
| Wazuh native rule | this section | Wazuh manager, real-time | runs inside a real SIEM |


## Why a Sigma rule can't run on Wazuh directly

Sigma is designed to be portable across SIEMs via converters that translate it into each vendor's language. Those SIEMs work by **querying logs already indexed and stored**. Wazuh works differently: it **decodes the raw log into fields, then matches XML rules in real time as the log passes through the manager**. The detection models differ, so there is no official Sigma→Wazuh backend (community ones exist but are not stable).

This is not a flaw in Sigma — it is a spec, not an engine. The detection logic was re-expressed as a native Wazuh rule.


## Detection logic — gate-first (parent / child)

- **Parent (gate)** — `event = login_attempt` **AND** `username` contains `'` → low level, just triggers children
- **Child / success** → `result = success` → **level 15 (critical)** — auth bypass succeeded, open incident immediately
- **Child / failed** → `result = failed` → **level 7 (medium)** — probing, monitor

The gate is checked once in the parent; children match only after the parent matches (`if_sid`). This keeps the `'` condition in one place (DRY) and — most importantly — filters on the **root indicator (`'`), not on the result**.

See [`local_rules.xml`](./local_rules.xml).


## Files in this section

| File | What it is |
|------|-----------|
| `local_rules.xml` | the 3 custom rules (gate + 2 severity children) |
| `localfile-snippet.xml` | the `<localfile>` block that tells Wazuh to read the lab log as JSON |
| `compose-volumes-snippet.yml` | the two volume mounts that feed the log and rule into the manager |
| `screenshots/` | logtest + dashboard + pipeline evidence |


## How to reproduce

1. Start a Wazuh 4.9.0 single-node stack (official `wazuh/wazuh-docker`).
2. Add the two mounts from `compose-volumes-snippet.yml` to the `wazuh.manager` service.
   **Note:** the host path is absolute — change it to match your own environment.
3. Add the block from `localfile-snippet.xml` inside an `<ossec_config>` in `wazuh_manager.conf`.
4. Place `local_rules.xml` at `/var/ossec/etc/rules/local_rules.xml` (mounted via the snippet).
5. `docker-compose down && docker-compose up -d`, then generate login traffic against the Section 01 lab.

> Wazuh 4.9.0 decodes JSON fields **flat** (`username`, `result`), without a `data.` prefix — confirm field names in `wazuh-logtest` Phase 2 rather than assuming. The dashboard displays them as `data.username`.

## Test cases & results

Verified in **both** `wazuh-logtest` and the live pipeline (login traffic → logcollector → analysisd → alert).

| # | username | result | has `'`? | outcome |
|---|----------|--------|----------|---------|
| 1 | `'OR 1=1-- -` | success | yes | **critical** (rule 100011, level 15) |
| 2 | `' OR 1=2-- -` | failed | yes | **medium** (rule 100012, level 7) |
| 3 | `admin` | success | no | no alert ✅ |
| 4 | `admin` | failed | no | no alert ✅ |

**Case 3 is the key proof.** It has `result = success`, identical to the critical case — the only difference is the absence of `'`. It stays silent, proving the rule keys on the root indicator, not the result. Had `result` been the gate, every successful user login would become a false positive.

## Screenshots

- `01-logtest-critical.png` — case 1 fires rule 100011 (level 15) in logtest
- `02-logtest-benign-admin.png` — `admin` stops at Phase 2, no rule match (gate filtered it)
- `03-dashboard-alert.png` — alert shown on the Wazuh dashboard
- `04-pipeline-alert-json.png` — the alert in `alerts.json` from the live pipeline


## Known limitations & lessons

- **logtest ≠ pipeline.** logtest feeds logs straight into `analysisd`; the live pipeline must pass through `logcollector` first. A rule can pass logtest yet produce no alert if `logcollector` isn't picking up new lines.
- **File-offset on WSL2 bind mount.** `logcollector` tails from the offset where it started and, across a WSL2 bind mount, can miss appended lines. Restarting the manager resets the offset. Generate the attack *after* the restart.
- **Retention.** Alerts are not permanent — Wazuh rotates log files daily and the indexer applies index retention, so old alerts disappear from the dashboard over time. Real deployments need a retention/archive strategy.
