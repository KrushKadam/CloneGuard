# CloneGuard — Attack Surface

## (a) File Uploads

**What's exposed:** Two `st.file_uploader` widgets (Check a call, Enroll a voice) accept WAV files from the browser.

**Current controls:**
- `max_upload_size=25` on both widgets (`app.py` lines 414, 578)
- `save_upload()` hard guard: raises `ValueError` if `len(data) > 25 * 1024 * 1024` (`app.py` line 123)
- WAV header validation via `wave.open()` after write (`app.py` lines 129–136)
- Random temp filenames via `tempfile.mkstemp(prefix="cg_ui_")` (`app.py` line 71)
- Files written to OS temp dir (`cloneguard_ui/`), not project dir

**Residual risk:** 25 MB limit is generous for phone audio (~4 min at 48 kHz 16-bit mono). A malformed WAV that passes header check but crashes downstream parser is theoretically possible but low likelihood.

**Recommendation:** Consider lowering limit to 10 MB (covers typical call recordings). Add MIME sniff as defense-in-depth.

---

## (b) Localhost HTTP Port 8501

**What's exposed:** Streamlit serves the UI on `http://localhost:8501`. Bound to loopback only by default.

**Current controls:**
- Streamlit default binds to `localhost` (not `0.0.0.0`) — verified in `app.py`, no `server.address` config override
- No authentication (single-user desktop tool assumption)
- No CORS configuration (same-origin only)
- No XSRF tokens (not an API)

**Residual risk:** Any process on the same machine can reach the UI. On shared multi-user systems, other local users could interact with the app. No sensitive actions are destructive (enroll/replace voiceprint, run check, generate report).

**Recommendation:** Document that the app is for single-user trusted devices. If multi-user isolation is needed, run in a container or VM.

---

## (c) Environment / Registry Key Storage

**What's exposed:** `GNANI_API_KEY` read from process environment first, then Windows registry `HKCU\Environment` (`voiceprint.py` lines 39–55).

**Current controls:**
- Key never written to files by app code
- `api_key_present()` only returns boolean (`app.py` line 66)
- README warns against pasting into terminal (shell history) and recommends system env var (`README.md` line 71)

**Residual risk:** Registry fallback is a deliberate accepted risk (audit finding LOW). If key is set via terminal paste, it remains in shell history. Registry is per-user but readable by any process in the user context.

**Recommendation:** Remove registry fallback after contest deadline. Use system environment variable exclusively. Consider Windows Credential Manager for future versions.

---

## (d) Disk Persistence (`data/`, `reports/out/`)

**What's exposed:** JSON files store voiceprints (biometric), incidents (transcripts, PII), caches. PDF reports contain derived evidence.

**Current controls:**
- `.gitignore` excludes all `data/` JSON files and `reports/out/` (`.gitignore` lines 4–9)
- App handles missing files gracefully (returns `[]` in `load_incidents()`, `load_voiceprints()`)
- No encryption at rest (local-only threat model)

**Residual risk:** Other local users with filesystem read access can view biometric data and transcripts. OS file permissions are the only barrier.

**Recommendation:** For shared machines, set restrictive ACLs on `data/` and `reports/out/`. Consider encrypting `voiceprints.json` with a user-derived key.

---

## (e) Public Git Repository

**What's exposed:** Source code, documentation, sample audio, configs pushed to public GitHub.

**Current controls:**
- `.gitignore` blocks `.env`, all `data/*.json`, `reports/out/`
- No real secrets in git history (scan found only placeholder `your-key-here`)
- Sample audio is synthetic (generated via Timbre), not real people
- `requirements.txt` pins versions (supply-chain hygiene)

**Residual risk:** None identified. Repo is safe to publish.

**Recommendation:** Run `git log -p --all | grep -iE "(cfut_|cfat_|GNANI_API_KEY\s*=\s*\S{20,})"` before every push.

---

## (f) Dependencies

**What's exposed:** Six pinned packages in `requirements.txt`.

**Current controls:**
- All versions pinned (`fpdf2==2.9.0`, `fonttools==4.68.0`, `pypdf==7.0.0`, `requests==2.34.2`, `streamlit==1.66.1`, `uharfbuzz==0.57.0`)
- `pip install --dry-run` verified exit 0
- No `pickle`, `eval`, `exec` in codebase (single subprocess = fixed-arg `pip install fpdf2` in `selftest/scorecard.py`)

**Residual risk:** Transitive dependencies not pinned. Streamlit ecosystem pulls many packages.

**Recommendation:** Periodic `pip-audit` or `pip list --outdated`. Consider `pip-tools` for full lockfile.

---

## (g) Outbound API Calls

**What's exposed:** HTTPS POST to `https://api.vachana.ai` for embeddings, STT, TTS. API key sent in `X-API-Key-ID` header.

**Current controls:**
- URLs hardcoded in `voiceprint.py` (`BASE`) and `gnani.py` (`BASE`) — no SSRF vector
- Timeout 120s (embeddings), 60s (STT/TTS)
- Key never logged (only boolean presence check)
- Error messages sanitized in `readable_error()` (`app.py` lines 76–115) — no key leakage

**Residual risk:** Network eavesdropper on untrusted Wi-Fi could see metadata (destination, timing) but not payload (TLS). API key in header is encrypted by TLS.

**Recommendation:** Use trusted network. For high-sensitivity environments, consider VPN or corporate egress proxy.

---
*Attack surface documented 9 November 2026. File refs match `app.py`, `voiceprint.py`, `gnani.py`, `config.py`, `.gitignore` at commits `1cdeb5a`, `8d0deb6`.*