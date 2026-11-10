# CloneGuard — Solution Pitch (one page)

**In one line:** CloneGuard checks whether a caller's voice matches a trusted enrolled person and scans the conversation for Hinglish scam patterns, then shows both pieces of evidence with a plain-English risk verdict.

## Problem

Families across India receive scam calls in Hinglish that sound like a parent, a sibling, a colleague. Enterprise voice-security products are reached through sales contracts; a regular caller has no practical way to verify a claimed identity against someone they trust.

## Solution — two visible layers, one score

- **Layer 1 — claim-routed voiceprint verification.** Gnani Voice-Clone embeddings (768 numbers per voice) of the caller are compared by cosine similarity against the enrolled voiceprint of the claimed person (threshold 0.55). Spoken claim phrases such as "main Papa bol raha hoon" route the check to the correct voiceprint.
- **Layer 2 — Hinglish transcript scan.** 32 dual-script rules (204 variants, Latin + Devanagari) across six red-flag categories — urgency, OTP requests, authority claims, threats, emotional pressure, deceptive calls to action — scanned over the Gnani Prisma transcript.
- **Composite verdict.** Equal-weight combination banded Low / Caution / High, with both layer scores, matched phrases and the transcript excerpt visible; a per-check PDF evidence report and a dated incident log.

## Proof — Self-Test Harness (10 generated scenarios, known answers)

- Scam calls caught: **7 / 7** (all High risk) · Genuine calls passed: **3 / 3** (all Low risk) · Cautions: **0** · Errors: **0**
- Threshold sweep 0.45–0.65: **flat** — every setting returned 7/7 and 3/3
- Voiceprint separation: same-speaker cosine **0.7306** vs different-speaker **0.2964**
- A fresh-machine end-to-end run, the project report and the full test recording are archived in the repository.

## Stack

Python · Streamlit (local interface) · Gnani Prisma (speech-to-text) · Gnani Timbre (text-to-speech, spoken verdict) · Gnani Voice-Clone embeddings · fpdf2 (PDF reports) · JSON storage. Local interface, cloud inference — an internet connection is required.

## Known limitations

1. A perfect clone of the enrolled voice passes Layer 1.
2. A mismatch is not proof of synthetic audio — it flags an identity mismatch.
3. Analysis runs on Gnani's cloud; audio leaves the machine.
4. "No scam patterns found" means no phrase matched the list, not that the call is safe.

## Team and links

Built by **KrushKadam** and **Legendry-Sannin (Om Aswar)** for the Gnani AI — Great Indian AI Internship Challenge, November 2026.

- Repository: https://github.com/KrushKadam/CloneGuard
- 60-second demo video: `artifacts/videos/cloneguard-linkedin-demo.mp4`
- Full end-to-end test run: `artifacts/videos/cloneguard-e2e-test-full.mp4`
- Project report (15 pages): `artifacts/CloneGuard-Project-Report.pdf`