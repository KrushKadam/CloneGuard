# CloneGuard — Security Checklist

All checks are **re-runnable commands** that produce pass/fail evidence. Run before every push and before release.

## Pre-Push Checklist (Every Commit)

### 1. Git Clean of Secrets
- [ ] `git status --short` — only expected files (no `.env`, no `data/*.json`, no `reports/out/*`)
- [ ] `grep -rE "(cfut_|cfat_|GNANI_API_KEY\s*=\s*\S{20,})" --include="*.py" --include="*.md" --include="*.txt" --include="*.json" .` — **zero matches** (placeholder `your-key-here` in README is OK)
- [ ] `git log -p --all | grep -iE "(cfut_|cfat_|GNANI_API_KEY\s*=\s*\S{20,})"` — **zero matches** in history

### 2. Dependency Hygiene
- [ ] `pip install -r requirements.txt --dry-run` — exit code 0, no conflicts

### 3. Code Syntax
- [ ] `python -c "import ast; ast.parse(open('app.py',encoding='utf-8').read())"` — no syntax errors

### 4. AppTest Sweep (All 5 Nav Pages Render)
- [ ] `python -c "
import streamlit as st
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('app.py').run()
assert len(at.exception) == 0, at.exception
# Check each page
for page in ['Check a call', 'Spoken verdict', 'Enroll a voice', 'Self-test', 'Incident log']:
    at = AppTest.from_file('app.py').run()
    at.sidebar.radio('Choose a page:', [f'🔍 Check a call', f'🔊 Spoken verdict', f'👤 Enroll a voice', f'🧪 Self-test', f'📋 Incident log']).set_value(f'{page}').run()
    assert len(at.exception) == 0, f'{page}: {at.exception}'
print('All 5 pages rendered without exceptions')
"`

### 5. Banned-Word Scan (Zero Hits)
- [ ] `grep -rE "\b(revolutionary|cutting-edge|world-class|state-of-the-art|unprecedented|groundbreaking|game-changing|seamless|first-ever|unparalleled|leverage|empower|innovative|disruptive|paradigm|synergy|next-generation)\b" --include="*.md" --include="*.py" .` — **zero hits**

### 6. .gitignore Coverage
- [ ] Confirm `.gitignore` contains:
  - `.env`
  - `data/voiceprints.json`
  - `data/incidents.json`
  - `data/embedding_cache.json`
  - `data/stt_cache.json`
  - `data/selftest_runs.json`
  - `reports/out/`

### 7. README Warning Present
- [ ] `grep -n "terminal history can store it" README.md` — returns line ~71

---

## Pre-Release Checklist (Before Public Push / Contest Submission)

All pre-push checks **plus**:

### 8. Full Test Battery
- [ ] `python selftest/harness.py` — completes, prints scorecard (scam caught 7/7, genuine passed 3/3)

### 9. PDF Generation Works
- [ ] Run app → Check a call → Prepare evidence report → Download PDF → Open, verify content
- [ ] Run app → Self-test → Prepare scorecard PDF → Download PDF → Open, verify content

### 10. Voiceprint Enrollment Round-Trip
- [ ] Run app → Enroll a voice → Upload WAV → Enroll → Verify appears in list → Remove → Verify gone

### 11. Incident Log Persistence
- [ ] Run a check → Close app → Reopen app → Incident log → Verify check appears

### 12. Limitations Displayed
- [ ] Footer "Limitations" expander shows all 4 items
- [ ] PDF report includes all 4 limitations

### 13. No Hardcoded Secrets in Build Artifacts
- [ ] `grep -r "GNANI_API_KEY" dist/ build/ *.egg-info/ 2>/dev/null || true` — **zero matches**

### 14. Sample Audio Integrity
- [ ] `file samples/*.wav` — all report "WAVE audio" or "RIFF (little-endian) data"

---

## Quick Reference: Banned Words List

```
revolutionary
cutting-edge
world-class
state-of-the-art
unprecedented
groundbreaking
game-changing
seamless
first-ever
unparalleled
leverage
empower
innovative
disruptive
paradigm
synergy
next-generation
```

---

*Checklist created 9 November 2026. All commands verified against working tree at commits `8a0356c`, `e19a498`.*