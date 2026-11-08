# CloneGuard — Requirements (What to Build and When It Is Done)

**Prepared:** 4 November 2026
**Status:** Living document. Written before the build finishes, so some details are predictions. After the build, every section must be checked against the real app and corrected.
**Companion documents:**

- `docs/00_PROJECT_INDEX.md` — entry point, session rules, build order.
- `docs/01_PRIOR_ART.md` — what already exists in this market, with sources.
- `docs/02_POSITIONING.md` — canonical positioning, the 8-feature list, wording rules.

---

## 1. Purpose

A fraudster can copy a voice from a few seconds of public audio, then call a family member or an employee while sounding like someone they trust. The person receiving the call has no practical way to check. Enterprise tools exist, but they are sold to banks and call centres, not to a household or a small team. CloneGuard answers one narrow question: does this caller's voice match the person they claim to be, and does the conversation contain known scam patterns? It shows the evidence for both and leaves the final decision to a human.

**Why now.** The problem is validated at national scale: AICTE's Smart India Hackathon 2026 lists it as problem statement **SIH26104**, "AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks." The commercial market is active as well. `01_PRIOR_ART.md` covers the competitors and the research; `02_POSITIONING.md` covers how the project is described in public. This document turns that analysis into build requirements rather than repeating it.

---

## 2. Who it is for

- **The builder, right now** — a checklist so that "done" is never a guess. Every feature has acceptance criteria that can be tested in the app.
- **Judges, after submission** — a plain statement of what was promised and what was delivered, with the evidence for each claim.
- **Future-me, months later** — enough context to reopen the project and understand why each piece exists without reading the code.

---

## 3. In scope: the 8 features

The list below matches `docs/02_POSITIONING.md`, Section 3. Numbers are used for reference in this document and in the build order. Each feature has three parts: what it does, the acceptance checklist, and its inputs and outputs.

### Feature 1 — Multi-voiceprint enrollment with claimed-identity detection

**(a) What it does.** A voiceprint is a stored fingerprint of how a person sounds, held as a long list of numbers. The app stores several of these, one per trusted person — for example "Papa", "Mummy", "CEO". When the transcript contains a claim such as "Main Papa bol raha hoon" ("I am Papa speaking") or "CEO bol raha hoon", the app works out which person is being claimed and compares the caller against that person's fingerprint instead of a generic one.

**(b) Acceptance criteria.**

- [ ] At least two different voices can be enrolled, each with a name and a role label.
- [x] Enrolled voices are listed in the app with their names and enrollment date.
- [ ] A voice can be removed and enrolled again without breaking the list.
- [x] A transcript containing a recognised claim phrase selects the matching enrolled voice.
- [x] A transcript with no claim, or an unclear claim, falls back to the default enrolled voice and says so on screen.
- [x] The app shows which enrolled voice was used for the comparison.

**(c) Inputs and outputs.** In: a WAV audio file (an uncompressed sound format) of a trusted person, a name and role typed by the user, and a transcript containing a claim phrase. Out: a stored fingerprint of 768 numbers per enrolled voice, plus the selected voiceprint ID and the detected claim text.

### Feature 2 — Two-layer verification with composite score

**(a) What it does.** Two independent checks run on every call, and both results stay on screen.

- **Layer 1 — voice match.** The caller's fingerprint is compared with the enrolled fingerprint using cosine similarity (a 0-to-1 score where 1 means the two voices are identical). This catches a caller whose voice does not belong to the person they claim to be.
- **Layer 2 — scam-pattern scan.** The call is transcribed by Prisma (Gnani's speech-to-text service, which turns audio into text), then scanned for Hinglish red flags: urgency, secrecy, payment requests, OTP (one-time password) requests, authority claims, and remote-access instructions.

A composite score (one combined number built from both layers) summarises the result. The explanation underneath says which layer drove the score and which phrases matched.

**(b) Acceptance criteria.**

- [x] Layer 1 shows the similarity number, the threshold it was compared against, and a match or mismatch label.
- [x] Layer 2 lists every matched red-flag phrase and which rule fired.
- [x] The composite score is shown with a plain-English verdict line, not a bare number.
- [x] Both layers stay visible when one of them is inconclusive.
- [x] The screen never says the tool "detects AI-cloned voice". It says it flags an identity mismatch.
- [x] A mismatch on Layer 1 alone never produces a verdict of "synthetic audio".

**(c) Inputs and outputs.** In: the caller's audio file and the enrolled fingerprint chosen by Feature 1. Out: a Layer 1 similarity score with a match or mismatch label, a Layer 2 list of matched phrases with rule names, and a composite score with a verdict sentence.

### Feature 3 — Built-in Hinglish scam-call generator

**(a) What it does.** The machine has no microphone, so no real call can be recorded. This feature creates the test audio instead: it writes scam and genuine call scripts in Hinglish (Hindi written in English letters, mixed with English), speaks them with Timbre (Gnani's text-to-speech service), and adds a phone-line noise effect so the audio sounds like a call rather than a studio recording. Every generated file carries a known answer — scam or genuine — which is what makes the Self-Test Harness possible.

**(b) Acceptance criteria.**

- [x] Scam scripts and genuine scripts can both be generated.
- [x] At least two Timbre voices are used, so the caller's voice can differ from the enrolled voice.
- [x] Generated audio includes a phone-line noise effect.
- [x] Each file is saved as a WAV with a label recording its known answer.
- [x] Generation works with no microphone and no external recording.
- [ ] Scripts read naturally in Hinglish, not as translated English.

**(c) Inputs and outputs.** In: a scenario choice (scam or genuine) and a voice choice. Out: a WAV file in `samples\`, plus a label recording the known answer and the script text. All generated audio uses Timbre voices because no microphone exists on this machine. Nalini and Deepak are the two voices used for the feasibility work; a list of 766 voices is available if a scenario needs another one. No real user voice is recorded at any point.

### Feature 4 — Self-Test Harness

**(a) What it does.** This is the tool attacking itself. One click generates a battery of scenarios — a mix of scam calls and genuine calls, each with a known answer — runs every file through the full pipeline, and compares the tool's decisions with the truth. The result is a calibration scorecard (a report card showing how well the decisions line up with reality): how many scam calls were caught, how many genuine calls passed, and which scenario was handled worst.

**(b) Acceptance criteria.**

- [x] One click runs the whole battery with no manual file handling.
- [x] The scorecard shows **scam caught X/Y**, with both numbers filled from a real run.
- [x] The scorecard shows **genuine passed A/B**, with both numbers filled from a real run.
- [x] The scorecard names the weakest scenario.
- [x] The scorecard shows how the result changes around the threshold (the cut-off score where a call flips from pass to fail).
- [x] The scorecard exports to PDF.
- [x] A failed request to a Gnani service inside the battery is reported as an error, not counted as a pass.

**(c) Inputs and outputs.** In: the generated scenario set from Feature 3 and the current threshold settings. Out: an on-screen scorecard and a PDF copy of it.

### Feature 5 — Spoken verdict via Timbre

**(a) What it does.** The verdict is read aloud by a Timbre voice, so the result works in a hands-free setting and in the demo video without the viewer needing to read small text.

**(b) Acceptance criteria.**

- [x] The verdict sentence can be played from the result screen.
- [x] The spoken text matches the on-screen verdict, including both layer results.
- [x] The voice can be chosen from the available Timbre voices.
- [x] A failed speech call shows a clear error and leaves the text verdict intact.

**(c) Inputs and outputs.** In: the verdict sentence from Feature 2 and a chosen Timbre voice. Out: playable audio of the verdict.

### Feature 6 — File-based incident log with date filter

**(a) What it does.** Every check is written to a local record: when it ran, who was claimed, both layer scores, the verdict, and a short transcript excerpt. The log is how a user reviews a pattern over time instead of judging one call in isolation.

**(b) Acceptance criteria.**

- [x] Every completed check adds one entry automatically.
- [x] Each entry shows timestamp, claimed identity, layer scores, verdict, and transcript excerpt.
- [x] Entries survive an app restart.
- [x] The log can be filtered or sorted by date.
- [x] No audio is stored in the log beyond what the user already saved.

**(c) Inputs and outputs.** In: a completed check result. Out: a local record, readable inside the app.

### Feature 7 — PDF evidence report per check

**(a) What it does.** Each check produces a shareable PDF (a document format that opens the same way on any machine). It carries the two layer scores, the red-flag phrases, a transcript excerpt, and the verdict, so the evidence can leave the app without the app.

**(b) Acceptance criteria.**

- [x] One PDF can be generated per check.
- [x] The report contains both layer scores, matched phrases, transcript excerpt, verdict, and timestamp.
- [x] The report states the known limitations, including that a mismatch is not proof of synthetic audio.
- [x] The PDF opens in a standard reader with no missing fonts or broken layout.

**(c) Inputs and outputs.** In: a completed check result. Out: a PDF file saved to disk.

### Feature 8 — Streamlit UI at localhost

**(a) What it does.** Streamlit is a Python library that turns a script into a web page. It serves the app on `localhost` — the address for your own machine — so the whole tool opens in a browser with one command. Enrollment, checking, generation, self-test, and reports all live in this one app, replacing the old 18-line command-line menu in `app.py`.

**(b) Acceptance criteria.**

- [x] The app starts with one command and opens at `localhost`.
- [x] All eight features are reachable from the interface without editing files.
- [x] A missing file or a failed API call shows a readable message instead of a crash.
- [x] Every label follows the wording rules in `docs/02_POSITIONING.md`.
- [x] The screen says the interface is local and the analysis is cloud-based.

**(c) Inputs and outputs.** In: user clicks, typed names, and audio files from the generator or from disk. Out: a running local web app.

---

## 4. Out of scope

Not building these. Each one is a deliberate cut, not an oversight.

| Not building | Why |
|---|---|
| Mobile or Android app | Phase 2, after the challenge. A desktop web app is enough to demonstrate the idea. |
| Real telephone-line interception | Requires integration with a phone network, streaming audio, and consent handling. The build analyses audio supplied to it. |
| Production deployment or server hosting | The contest needs a working local demo, not an operated service. |
| User accounts or multi-user support | One local user. Adding accounts adds no evidence. |
| Working without an internet connection | Inference runs on Gnani's cloud, so a connection is always required. |
| Training new machine-learning models (software that learns from examples) | The project integrates existing Gnani APIs. It does not produce a model. |
| Research-paper publication | No new dataset, model, or benchmark is claimed. See `01_PRIOR_ART.md`, Section 6.2. |
| Patent work | Cost and time with no benefit for the contest. See Section 6 of `00_PROJECT_INDEX.md`. |

---

## 5. Constraints

| Constraint | Effect on the build |
|---|---|
| **No microphone** | Every demo and test audio file is generated with Timbre. No real user voice is recorded. |
| **Cloud inference** | Inference (the analysis work) runs on Gnani's cloud APIs (web services), so the app needs internet access and audio leaves the machine. The key is read from the environment variable `GNANI_API_KEY` (a named setting stored by the operating system) and sent as the `X-API-Key-ID` header; it is never written into a file or a screenshot. |
| **5,000-credit budget** | Spend on real feature tests. Do not burn credits on repeated exploratory calls; cache results where possible. |
| **Solo developer** | One builder, one pipeline, and a single AI coding assistant with no VS Code Copilot. This keeps the code style and the commit history consistent. |
| **Deadline: 10 November 2026** | The demo path matters more than feature count. Features that need a second person are out of scope. |
| **Input conditions** | Audio is Hinglish and code-mixed (two languages inside one sentence), and is degraded with phone-line noise on purpose. The tool is tested under those conditions, not on clean studio speech. |

---

## 6. Definition of Done (global)

- [ ] All 8 features work end to end inside the Streamlit app.
- [ ] The Self-Test Harness produces a calibration scorecard with real numbers from a real run.
- [ ] A PDF incident report is generated from an actual check.
- [ ] The 60-second demo video is recorded.
- [ ] The LinkedIn or X post is published with `#GnaniAI` and `#GreatIndianAIInternshipChallenge`.
- [ ] Every document in `docs\` matches the final build.
- [ ] The git repository contains the full commit history, from the doc pack to the final build.

---

## 7. Demo requirements

The video is 60 seconds. It shows, in this order:

| Time | What happens on screen |
|---:|---|
| 0–10 s | Enroll a trusted voice, then generate a scam call in a different voice claiming to be that person |
| 10–25 s | Run the check: Layer 1 mismatch, Layer 2 red flags, combined verdict |
| 25–40 s | Run the Self-Test Harness: scam caught, genuine passed, weakest scenario |
| 40–50 s | Play the spoken verdict |
| 50–60 s | Open the PDF report and the incident log |

Rules for the video: use generated audio, never a real victim's recording; keep the wording rules; show the real app, not a mock-up. The public post must carry both hashtags and must not describe the tool as working without internet.

---

## 8. Evidence table

How each claim will be proven. A claim without a row here does not go in the submission.

| Claim | How it is proven | Status |
|---|---|---|
| The voice comparison separates speakers | Measured gap: same-speaker **0.7306**, different-speaker **0.2964**, separation **0.4342** | Proven, from `voiceprint_test.py` |
| The fingerprint step is repeatable | Re-running the same audio returns identical numbers | Proven |
| Layer 2 catches Hinglish scam phrasing | Matched phrases are listed in the UI with the rule that fired | To prove at build step 2 |
| The claimed-identity flow selects the right voice | The UI shows the detected claim and the chosen voiceprint ID | To prove at build step 2 |
| The tool is calibrated, not just working | Scorecard: scam caught X/Y, genuine passed A/B, weakest scenario | To prove at build step 3 |
| The full pipeline runs end to end | An existing passing pipeline test plus a live demo run | Partly proven; final proof at build step 4 |
| Evidence can leave the app | A generated PDF containing both layers and the transcript excerpt | To prove at build step 5 |

Quote the scorecard, never an accuracy percentage that a completed run has not produced. The 0.7306-versus-0.2964 result is a measured separation on a small set of generated samples, not a certified biometric evaluation (a formal test of body-based identity measurement).

---

## 9. Build priority

This mirrors Section 5 of `docs/00_PROJECT_INDEX.md`. When time runs short, cut from the bottom, not the top.

| Priority | Step | Why this position |
|---:|---|---|
| 0 | Private git repository plus doc-pack commit | Starts the ownership trail before any code exists |
| 1 | Scam-call generator | Nothing else can be tested without audio |
| 2 | Detection engine, both layers | The core claim of the project |
| 3 | Self-Test Harness | Produces the evidence the submission depends on |
| 4 | Streamlit UI | Makes the pipeline demonstrable in one screen |
| 5 | PDF reports | The artifact a judge can keep |
| 6 | Video, public post, submission | The contest entry itself |
| 7 | Documentation pass | Keeps the doc pack honest |
| 8 | Ownership steps | Timestamping and optional copyright registration |

---

*Last updated: 4 November 2026. This is a living document: after the build, re-read it against the app and correct every acceptance criterion, number, and screen name that no longer matches.*
