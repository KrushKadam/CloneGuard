# CloneGuard — End-to-End Test Prompt (fresh machine)

Paste everything below the line into Claude Code from the repo root. It runs a
complete test on Linux with no audio supplied by the operator — the repo ships
labeled test audio. Expected API usage: ~30-50 calls (credits); ~10-20 minutes.

---

## Your mission

Test CloneGuard end to end and produce a PASS/FAIL report. CloneGuard is a desktop
tool that checks whether a caller's voice matches a trusted enrolled person
(Layer 1 — voiceprint cosine similarity, threshold 0.55) and scans the transcript
for Hinglish scam patterns (Layer 2 — 32 dual-script rules across six categories).
Both layers combine into a 0-100 score banded Low / Caution / High. The interface
runs locally; analysis runs on Gnani's cloud APIs, so internet is required.
Context entry point: docs/00_PROJECT_INDEX.md.

## Hard rules

1. NEVER print, echo, or log the value of GNANI_API_KEY. Presence check only (YES/NO).
2. Count and report every Gnani API call you make — those are the project's credits.
3. Do NOT modify code. Do NOT commit. Do NOT push. Local changes under data/
   (caches, voiceprints.json, incidents.json) are expected and fine (gitignored).
4. A defect gets documented with evidence and a proposed fix in the report — never
   applied by you.
5. Any text you write must follow docs/02_POSITIONING.md Section 2 wording rules:
   never "detects AI-cloned voice", never "offline"/"on-device", no superlatives.

## Environment setup (Linux)

- python3 --version (3.14+ expected; streamlit is pinned at 1.66.1)
- python3 -m venv .venv && source .venv/bin/activate
- pip install -r requirements.txt
- GNANI_API_KEY must already be set by the operator. If missing, STOP and tell the
  operator: export GNANI_API_KEY="<key>" (shell or .bashrc), then re-run. Verify
  presence with:
  python3 -c "import os; print('Key loaded:', 'YES' if os.environ.get('GNANI_API_KEY') else 'NO')"

## Phase 0 — Preflight (0 credits)

python3 READY_CHECK.py
Expected: "Key loaded: YES", "Gnani API: REACHABLE (422 expected, key accepted)",
"STATUS: CONNECTED". The 422 is a deliberate incomplete request that costs no
credits; it proves key + endpoint + internet. FAILED -> stop and report.

## Phase 1 — Static checks (0 credits)

1. python3 -m py_compile on every tracked .py file -> all OK.
2. Wording scan of app.py: "AI-cloned voice"=0, "detects AI-cloned"=0,
   "deepfake"=0, "synthetic"=1. Report actual counts; flag deviations.
3. Palette scan: every #hex in app.py must be in {#000000 #050505 #0a0a0a
   #ffffff #e5e5e5 #9ca3af #6b7280 #2eff6a #1cc24b #62ff94} plus
   rgba(255,255,255,x) / rgba(46,255,106,x). Report illegal count (expect 0).

## Phase 2 — UI smoke test (0 credits, no API calls)

1. Temp AppTest script (streamlit.testing.v1.AppTest.from_file("app.py")) that:
   - clicks nav_0..nav_4 by button key (labels: Check a call, Spoken verdict,
     Enroll a voice, Self-test, Incident log), asserting 0 exceptions per page and
     session_state["page"] matching;
   - asserts len(at.radio)==0;
   - clicks cta_open_check -> lands on "Check a call".
   Delete the temp script after. Expect: PASS, zero exceptions.
2. Optional: streamlit run app.py --server.headless true in background ->
   curl -sf -o /dev/null -w "%{http_code}" http://localhost:8501 -> expect 200 ->
   kill the server.

## Phase 3 — Functional end-to-end (fresh clone: no voiceprints, no caches)

Enroll FIRST — a fresh clone has no data/voiceprints.json (gitignored), and every
Layer 1 comparison needs one.

a) ENROLL (~1 call): enroll samples/A1_nalini_X.wav as name "Nalini", role "Papa".
   Use the app path if AppTest can drive the file uploader; otherwise call the
   enrollment function in voiceprint.py directly and note the substitution.
   Verify data/voiceprints.json now has 1 record with role Papa.
b) SCAM CHECK (~2 calls): samples/gc_scam_family_emergency*.wav (script says
   "main Papa bol raha hoon"). Expected: claim detected -> Papa voiceprint;
   Layer 1 mismatch and/or Layer 2 red-flag phrases listed; composite >= 60 ->
   HIGH risk; incident log gains one entry.
c) GENUINE CHECK (~2 calls): samples/gc_genuine_friend_dinner*.wav. Expected:
   LOW risk band with the matching verdict sentence.
d) CLAIM ROUTING: samples/gc_scam_executive*.wav says "main CEO bol raha hoon"
   and no CEO is enrolled yet -> expect on-screen note "claim names someone not
   enrolled" (fallback to the default voiceprint). Verify from result text.
e) INCIDENT LOG (0 calls): data/incidents.json has >= 3 records, each with
   timestamp, claim, both layer scores, verdict, transcript excerpt.
f) PDF (0 calls): generate the report for one check (app button or
   reports/incident_pdf.py directly). File exists, pypdf can read it, text
   contains both layer scores, verdict, and the four known limitations.
g) SPOKEN VERDICT (~1 call): produce spoken-verdict audio via the Timbre path;
   audio returned, on-screen verdict unchanged. If unavailable headless -> SKIP
   with reason.

## Phase 4 — Self-test battery (~15-25 calls; the calibration evidence)

Run the full battery (Self-test page button, or python3 selftest/harness.py).
Expected, from completed run run_20261107_183026_08f8: scam caught 7/7 (all High),
genuine passed 3/3 (all Low), caution 0, errors 0, threshold sweep flat across
0.45-0.65. On a fresh machine these are REAL API calls (no caches). Any deviation
is a finding to report as actual-vs-expected, not a failure of your testing.

## Phase 5 — Internet-sourced voice (operator supplies zero audio)

1. Source ONE license-clean voice recording, priority order:
   a. a WAV directly (Wikimedia Commons, archive.org public-domain, LibriVox);
   b. else CC0/CC-BY audio (e.g. Common Voice) IF ffmpeg exists (command -v ffmpeg)
      to convert to WAV.
   Record source URL, license, speaker description, format in the report.
   No establishable license -> do not use it; try another source or SKIP with reason.
   No ffmpeg and no WAV source -> SKIP this phase with reason (that is acceptable).
2. Convert if needed: ffmpeg -i in.ext out.wav -ar 16000 -ac 1 (must stay <= 25MB).
3. ENROLL it (~1 call) as name "InternetVoice", role "CEO".
4. RE-RUN samples/gc_scam_executive*.wav (~2 calls). Expected: claim "main CEO
   bol raha hoon" detected -> selects the CEO voiceprint (the internet voice);
   Layer 1 MISMATCH (Timbre scammer vs internet voice) + Layer 2 red flags ->
   composite >= 60 -> HIGH risk. This proves unknown-third-party voiceprint +
   claim routing + mismatch on audio the operator never provided.
5. State this honest limitation in the report: random internet speech contains no
   Hinglish scam phrases, so Layer 2 cannot be demonstrated on it; Layer 2 evidence
   comes from the repo's labeled samples (Phases 3b and 4).

## Phase 6 — Report

Write TEST_REPORT.md (local only, never committed) containing:
1. Table: Phase | Check | Expected | Actual | PASS/FAIL | Evidence (short snippet)
2. Total Gnani API call count for the session (the credit spend)
3. Defects: what, repro, observed vs expected (empty list if none)
4. One-line verdict, e.g. "E2E: 24/25 PASS, 1 SKIP (no ffmpeg), 0 defects"
5. Environment line: OS, python version, commit tested (git rev-parse --short HEAD)

Stop after the report. No fixes, no commits, no pushes.
