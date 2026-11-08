# CloneGuard — Contest Pack

**Prepared:** 8 November 2026  
**Contest:** Gnani AI Great Indian AI Internship Challenge  
**Deadline:** 10 November 2026  
**Mandatory hashtags:** `#GnaniAI` `#GreatIndianAIInternshipChallenge`

---

## PART 1 — LinkedIn / X Post

### LinkedIn version

A few seconds of public audio is enough to copy a voice. Families across India are getting scam calls in Hinglish that sound like a parent, a sibling, a colleague.

I built CloneGuard to give people a way to check. It does two things: it flags an identity mismatch between the caller and an enrolled voice, and it scans the transcript for Hinglish red-flag phrases — urgency, OTP requests, authority claims, threats, emotional pressure, deceptive calls to action. Both layers stay visible with a plain-English verdict.

The measured numbers from the Self-Test Harness (10 generated scenarios with known answers): 7 out of 7 scam calls caught, 3 out of 3 genuine calls passed. Zero cautions, zero errors. The result held flat across every threshold from 0.45 to 0.65. Voiceprint separation on the test set: same-speaker cosine 0.7306, different-speaker 0.2964, gap 0.4342.

Built on Gnani's Prisma (speech-to-text), Timbre (text-to-speech), and Voice-Clone embeddings. The interface runs locally at localhost; inference runs on Gnani's cloud.

Limitations I state upfront: a perfect clone of the enrolled voice passes Layer 1; a mismatch is not proof of synthetic audio; the app needs an internet connection; and "no patterns found" simply means the scan didn't match its list, not that the call is safe.

This is a working desktop tool, not a research claim. The demo runs end to end in 60 seconds: enroll, generate a scam call, check, self-test, speak the verdict, export the PDF.

#GnaniAI #GreatIndianAIInternshipChallenge

---

### X variant (≤280 chars)

Built CloneGuard: checks caller voice vs enrolled person + scans Hinglish for scam patterns. 7/7 scams caught, 3/3 genuine passed. Local UI, cloud inference via Gnani Prisma/Timbre. Limits stated. Demo in 60s. #GnaniAI #GreatIndianAIInternshipChallenge

---

## PART 2 — 60-Second Video Script

**Total spoken words: ~148**

| Time | On screen (Streamlit UI) | Narrator (spoken) |
|------|---------------------------|-------------------|
| 0:00–0:10 | Enroll page: add "Papa" with a WAV. Generator page: pick scam scenario, voice "Deepak", generate. | "Enroll a trusted voice. Generate a scam call in a different voice claiming to be that person." |
| 0:10–0:25 | Check page: run the check. Layer 1 shows mismatch (0.31 vs 0.55 threshold). Layer 2 lists matched phrases: "turant paisa bhejo", "OTP batao", "police ka case". Composite 74 — High risk. | "Layer 1: voice mismatch. Layer 2: Hinglish red flags matched. Combined verdict — high risk." |
| 0:25–0:40 | Self-Test page: click Run Harness. Scorecard appears: Scam caught 7/7, Genuine passed 3/3, Caution 0, Errors 0. Threshold sweep flat 0.45–0.65. Weakest scenario named. | "Self-Test Harness runs the battery. Seven scams caught, three genuine passed. Stable across thresholds." |
| 0:40–0:50 | Spoken Verdict page: click Play. Timbre voice reads: "High risk. The caller does not match Papa's voice. Scam patterns include urgency and OTP request." | "The verdict spoken aloud — same words, hands-free." |
| 0:50–1:00 | PDF report opens: both layer scores, matched phrases, transcript excerpt, verdict, limitations. Incident Log page shows the new entry with timestamp. | "PDF evidence report and incident log — shareable, dated, with every limitation included." |

---

## PART 3 — Submission Answers (Form-Style Q&A)

### What it does
CloneGuard is a desktop tool that checks whether a caller's voice matches a trusted enrolled person and scans the conversation for Hinglish scam patterns. It shows both pieces of evidence and a combined risk score, then leaves the final decision to a human.

### How it works
The caller's audio is sent to Gnani's Prisma service for transcription and to the Voice-Clone service for a 768-number voice fingerprint. Layer 1 compares that fingerprint against the enrolled voiceprint of the claimed person using cosine similarity (threshold 0.55). Layer 2 scans the transcript for 32 dual-script Hinglish red-flag patterns across six categories. A composite score (equal weights) maps to Low / Caution / High risk bands with a plain-English verdict. The interface runs locally at localhost; all inference runs on Gnani's cloud.

### What's different vs existing tools
- Consumer-facing desktop workflow (no sales contract, no enterprise integration)  
- Hinglish scam patterns written for code-mixed Indian contexts, not translated from English  
- Two independent layers (voice identity + transcript scan) that both stay visible with explainable arithmetic  
- Built-in Hinglish scam-call generator with phone-line noise for testing without a microphone  
- Self-Test Harness that attacks the tool and publishes a calibration scorecard with PDF export  
- Per-check PDF evidence report that includes both layer scores, matched phrases, transcript excerpt, verdict, and the four known limitations  
- Claimed-identity multi-voiceprint selection from spoken phrases like "Main Papa bol raha hoon"  

(No priority claims — these are feature-level differences from the comparison table in docs/06_INNOVATION_REPORT.md, Section 7.)

### Tech stack
Python, Streamlit (local web UI at localhost), Gnani Prisma (speech-to-text), Gnani Timbre (text-to-speech), Gnani Voice-Clone embeddings (768-dimension voice fingerprints), fpdf2 (PDF reports), JSON file storage in `data/`, runs locally with cloud inference.

### Measured results
All numbers from Self-Test Harness run `run_20261107_183026_08f8` (10 generated scenarios, known ground truth):
- Scam calls caught: **7 / 7** (all High risk)
- Genuine calls passed: **3 / 3** (all Low risk)
- Caution count: **0**
- Error count: **0**
- Threshold sweep (0.45, 0.50, 0.55, 0.60, 0.65): **flat** — all five settings returned 7/7 and 3/3
- Same-speaker cosine: **0.7306**
- Different-speaker cosine: **0.2964**
- Separation gap: **0.4342**
- Identity threshold used: **0.55**
- Scam phrase rules: **32 patterns, 204 variants** (Latin + Devanagari)
- Score weights: **0.5 / 0.5** (unchanged after calibration)
- Voiceprint size: **768 numbers**
- PDF report: **A4, native Devanagari, verified by text extraction**

Voice measurements from `voiceprint_test.py` (deterministic — same audio always produces same numbers). Self-Test Harness runs at 0 credits on this machine due to cached Prisma and embedding results.

### Limitations
1. **A perfect clone of the enrolled voice passes Layer 1.** Matching an identity is not proof that the audio is genuine.
2. **A mismatch is not proof of synthetic audio.** Layer 1 flags an identity mismatch between the caller and the enrolled voice. That catches clones and human impersonators alike. It does not, on its own, show that the audio was machine-generated.
3. **The analysis runs on Gnani's cloud.** Audio leaves the machine, and the app stops working without an internet connection. It is a local interface with cloud inference.
4. **A partial search cannot prove absence.** "No scam patterns found" simply means the scan did not match its phrase list. It does not mean the call is safe, and the app must never say that it does.

### What I'd build next
From docs/06_INNOVATION_REPORT.md, Section 9:
1. **Desktop background monitor** — a small process that watches audio the user supplies and raises the same two-layer signal without re-opening the app for each check.
2. **Public benchmark evaluation** — run the approach on ASVspoof-style test sets and IndicSynth (Indian-language synthetic speech dataset) instead of self-generated samples.
3. **Pattern-weight tuning from Self-Test data** — move Layer 2 weights and the identity cut-off from starting values to measured ones using the calibration harness output.

---

*End of contest pack. All claims map to measured evidence in the repository. No banned words used. Ready for submission.*