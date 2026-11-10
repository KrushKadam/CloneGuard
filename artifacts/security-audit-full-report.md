# CloneGuard Security Audit Report

## Run Profile and Scope

**Run type:** 6-phase security audit (full profile)  
**Target:** CloneGuard — local-only Streamlit desktop tool for voice impersonation and Hinglish scam detection in phone call recordings  
**Source reference:** Repository at commit used for this run  
**Execution boundary:** Source-only static review with sandboxed local execution for validation checks; no external network calls, no deployed endpoints  
**Prior run used:** `security/audit-2026-11-09.md` (commits `1cdeb5a`, `8d0deb6`) — four prior confirmed fixes carried as `prior_confirmed_same_source`; one accepted risk (registry fallback) carried; open recommendations mapped to deferred/out-of-scope units  
**Deferred / out of scope:** Encryption at rest for `voiceprints.json`, removal of registry fallback post-deadline, periodic `pip-audit`, upload limit reduction to 10 MB — all documented as accepted risk or deferred in prior run  
**Budget / agents:** Phase 1 recon by `nemotron-ultra` (Google models refused the task class); Phase 2 three isolated hunters (`deepseek-v4.1-flash`, `glm-5.3-flash`, `nemotron-ultra`) — Hunter A 11 units / 0 candidates, Hunter B 11 units / 0 candidates, Hunter C 10 units / 7 candidates; Phase 3 fresh adversarial verifier (`glm-5.3-flash-free`) rejected all 7; manager spot-checked 2 disputes, verifier correct on both; Phase 4 validators PASS; Phase 5 independent fresh session (`nemotron-3.5-lightning-30b`) verified every file:line claim — ALL_RECORDS_ACCURATE  

## Security Posture Summary

CloneGuard is a single-user, localhost-only desktop application with a clean trust boundary: the only external dependency is the Gnani cloud API over hardcoded HTTPS endpoints with TLS, authenticated by an API key stored in the user's environment or per-user Windows registry. No authentication or authorization model exists inside the app — the device owner has full control. All local persistence uses atomic `.tmp` + `os.replace` writes with append-only semantics for the incident log. The prior audit's confirmed fixes (`.gitignore` coverage, upload size guard, sample selectbox basename guard, `requirements.txt` creation) are present in the current source. No confirmed vulnerabilities were found in this run.

## Confirmed Findings

**No confirmed vulnerabilities in this run.** All 7 hunter candidates were independently rejected during adversarial verification.

## Needs Validation

**No records carry verdict `needs_validation`.** Zero validation plans are pending.

## Hardening Notes (Not Vulnerabilities)

- `app.py:860-869` inverted incident date-filter guard: unparseable timestamp would raise `AttributeError` on the History page (robustness bug, worth fixing).
- Success-path temp WAVs (uploads + TTS verdicts) are never deleted; accumulate in `%TEMP%\cloneguard_ui` across sessions (Hunter B).
- `selftest/harness.py:87` `_install_retry_wrappers()` installs permanently at import after first Self-test visit; bounded at 2x calls, never unwrapped (Hunter B).
- Prior `security/` docs in the repo overstated XSRF risk: Streamlit enables `enableXsrfProtection=true` by default; no override exists in the app (Hunter A correction).
- `engine/layer1.py:91` `except` clause misses `TypeError` for top-level non-dict JSON (robustness only).
- Cache keys use `int(mtime)` with 1s granularity; same-path rewrite within a second could serve a stale cached embedding/transcript — unreachable via app flows (fresh `mkstemp` per upload).
- `requirements.txt` pins 6 direct deps but has no lockfile (transitive deps float) — supply-chain hygiene for a local tool.
- `selftest/scorecard.py:152` runtime `pip install fpdf2` unpinned — dead code when `requirements.txt` is installed; hygiene only.
- Predictable `.tmp` sibling names, no cross-session lock: multi-tab last-writer-wins on `voiceprints.json` / `incidents.json`.
- `pipeline.py:162` `_load_incidents` accepts list only while `app.py:800` loader tolerates `{"records":...}` — a dict-form file would be silently replaced on next save (same-principal trigger only).

## Coverage Summary

**Ledger:** 32 coverage units planned, 32 covered, 0 gaps (validator PASS)  
**Hunter candidates:** 7 proposed (all by Hunter C), 0 from Hunter A, 0 from Hunter B  
**Verifier decisions:** 7 rejected, 0 confirmed, 0 needs_validation  
**Final critic result:** Clean coverage — all in-scope subsystems reviewed, no mandatory critic skipped  
**Important exclusions:** Web protocol/auth, client-side, cloud/deployment, RPC/messaging, desktop IPC, memory safety/binary, AI/LLM — all excluded with documented justification in `architecture.md`

## Limitations

- Source-only static review; no runtime fuzzing or dynamic analysis.
- Local single-user app — no multi-tenant or network-exposed attack surface.
- Prior audit `security/audit-2026-11-09.md` exists in the repo's `security/` folder and was used for revalidation mapping.
- Transitive dependency versions not locked; supply-chain risk limited to local install context.