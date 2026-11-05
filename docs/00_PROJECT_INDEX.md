# CloneGuard — Project Index (Start Here)

**Prepared:** 4 November 2026
**Status:** Living document. The plan below is correct as of the prepared date. It must be updated once the build is finished so that it describes what actually shipped, not what was planned.
**Companion documents:**

- `docs/01_PRIOR_ART.md` — what already exists in this market, with sources.
- `docs/02_POSITIONING.md` — the canonical description of the project, the 8-feature list, and the wording rules.
- `docs/03_REQUIREMENTS.md` — what to build, and how to tell when a feature is done.

---

## 1. What CloneGuard is

CloneGuard is a desktop tool that checks a phone call for signs of impersonation. It compares the caller's voice against a stored voice fingerprint of the person they claim to be, then reads the transcript for Hinglish (Hindi written in English letters, mixed with English) scam patterns. The screen shows both pieces of evidence and one combined risk score.

The interface runs locally at `localhost` (your own computer). The analysis itself runs on Gnani's cloud APIs (web services that do the voice and text work), so the app needs an internet connection.

---

## 2. Deadline and contest requirements

| Item | Detail |
|---|---|
| Deadline | **10 November 2026** |
| Required deliverable 1 | A working demo that runs end to end |
| Required deliverable 2 | A public post on LinkedIn or X |
| Required deliverable 3 | A 60-second video |
| Hashtags (mandatory) | `#GnaniAI` `#GreatIndianAIInternshipChallenge` |
| Contest | Gnani AI — Great Indian AI Internship Challenge |
| Team size | One person (solo build) |

The demo path and the video storyboard live in `docs/02_POSITIONING.md`, Section 3.2.

---

## 3. Document inventory

| File | What it is | Status | What it feeds |
|---|---|---|---|
| `00_PROJECT_INDEX.md` | This file. The entry point for anyone picking the project up. | Done (living) | Navigation, session rules, build order |
| `01_PRIOR_ART.md` | Competitor and research sweep with sources and fetch dates. | Done | Judge answers, "hasn't this been done?" section, README |
| `02_POSITIONING.md` | Canonical description, wording rules, 8-feature list, award mapping, demo path. | Done | Every public sentence: README, post, video script, submission |
| `03_REQUIREMENTS.md` | Plain-English requirements: what to build, acceptance criteria, evidence plan. | Done (living) | Build checklist, Definition of Done, submission answers |
| `04_ARCHITECTURE.md` | How the parts fit together: modules, data flow, API calls, failure handling. | Done (living) | Build steps 1–5 |
| `05_DATA_MODEL.md` | What is stored, where, and in what shape (enrolled voices, checks, incidents). Also holds the storage-engine recommendation. | Done (living) | Build steps 1–5, incident log, PDF reports |
| `06_INNOVATION_REPORT.md` | The narrative report: problem, approach, measured results, limitations. | Done (living). Section 6 awaits the build. | Submission, ownership evidence; Sections 1–5 and 7–10 drafted, Section 6 stubbed |
| `README.md` | The GitHub front page. Sits at the repository root and is the one document allowed outside `docs\`. | After build | Public repo landing page, judges |
| Contest pack (post + video script + submission answers) | The three public artifacts the contest asks for. Kept together in `docs\`. | After build | LinkedIn/X post, 60-second video, submission form |

**Halted for now (deliberately not written yet):**

| Item | Why it is paused | When it resumes |
|---|---|---|
| UI/UX visual design | The screens are easier to design once the working pipeline exists and the real labels are known. | During the build, at build step 4 |
| Decision log | Kept as one-line entries added as choices are made, not written in advance. | During the build, continuously |

---

## 4. Session rules

These rules apply to every document and every session on this project.

### 4.1 Plain English

Every document must be understandable by a non-technical person on the read-through. Short sentences. Everyday words. Every technical term gets a plain-English explanation the moment it appears.

**Before:**

> CloneGuard compares embeddings with cosine similarity to detect identity mismatch.

**After:**

> CloneGuard compares two voice fingerprints (called embeddings — long lists of numbers that describe how a voice sounds) using cosine similarity (a 0-to-1 score where 1 means the two voices are identical).

### 4.2 Banned words

Eight words are banned outright. A scan of every file must return zero matches. They are the words people reach for when they want a project to sound more important than it is.

| Group | What it looks like | Write this instead |
|---|---|---|
| Priority claims | saying the project did something before anyone else | name the build step or the date |
| Exclusivity claims | saying the project is the sole example | describe the feature and its evidence |
| Absence claims | saying no one has done this before | cite the prior art, then state the distinction |
| Hype | superlatives about scale, importance, or novelty | the measured number |

The literal list is kept in the session brief and enforced by the scan. It is not printed here, because printing it would break the rule it describes.

When a sentence wants one of those words, rewrite the sentence rather than deleting it. "Step 1" or "the starting step" carries the same meaning as a priority claim, without the claim.

### 4.3 Wording rules

`docs/02_POSITIONING.md`, Section 2 holds the full table. The two rules that matter most:

- Never describe the app as working without internet or as running on the device. The interface is local; inference (the actual analysis) is cloud-hosted.
- Never state that the tool "detects AI-cloned voice" as a fact. Say that it flags an identity mismatch between the caller and the enrolled voice.

### 4.4 Documentation sessions do not write code

A session that is asked to write or revise documents touches documents and nothing else. No code edits, no builds, no dependency installs. This keeps the documents reviewable on their own.

### 4.5 Living documents

These documents are written before the build finishes, so parts of them are predictions. After the build, every document gets a pass to match the final implementation: real screen names, real file names, real numbers from the Self-Test Harness, real limitations found along the way. A document that still describes a plan after the build is a bug.

### 4.6 Everything lives in `docs\`

No documentation files in the project root, with one exception: `README.md`, which is the GitHub front page and has to sit at the root to be displayed.

---

## 5. Build order for the original session

Follow this order. Each step produces something the next step can use.

0. **Start the repository.** Create a private git repository (a version-controlled folder that records every change) and commit the whole `docs\` folder before writing code. This is the starting point of the ownership trail.
1. **Scam-call generator.** Produce scam and genuine call scripts in Hinglish, spoken by Timbre voices (Gnani's text-to-speech service, which turns written text into audio) with a phone-line noise effect. Every test file comes from here, because the machine has no microphone.
2. **Detection engine, both layers.** Layer 1: enroll a voice, store its fingerprint, compare a new caller against it. Layer 2: transcribe with Prisma (Gnani's speech-to-text service) and scan for red-flag phrases. Combine into one score.
3. **Self-Test Harness.** One button that generates a battery of scenarios with known answers (scam or genuine), runs them through the full pipeline, and prints a calibration scorecard (a report card comparing what the tool decided with what was true).
4. **Streamlit UI.** Streamlit is a Python library that turns a script into a web page; it serves the app on `localhost`. Replace the old 18-line command-line menu in `app.py` with the real interface.
5. **PDF reports.** One shareable document per check (PDF opens the same way on any machine), containing both layer scores, the red-flag phrases, a transcript excerpt, and the verdict.
6. **Public artifacts.** Record the 60-second video, publish the LinkedIn or X post with both hashtags, submit the entry.
7. **Documentation pass.** Update every file in `docs\` to match the finished build.
8. **Ownership steps.** Run the post-build actions in Section 6.

---

## 6. Ownership proof actions

The goal is a dated, verifiable trail showing the work was yours and was done by the deadline.

| Action | What it gives you | Cost | When |
|---|---|---|---|
| Private git repository from day one | Every commit carries a date and a message. The commit history is a dated record of progress. | Free | Now |
| Milestone commits | One commit per finished feature or document. Each is a dated checkpoint. | Free | Throughout the build |
| Keep every draft and working file | The messy middle — half-written scripts, failed tests, notes — is the evidence of real work. Do not clean it up before submission. | Free | Throughout the build |
| Zip the project and timestamp it with OpenTimestamps | A free service that writes a cryptographic fingerprint of your file into a public blockchain, proving the file existed at that moment. Takes about two minutes. | Free | After the build |
| Copyright registration at `copyright.gov.in` | An official government record of authorship. | Small fee | Optional, after submission |
| The Innovation Report (`06_INNOVATION_REPORT.md`) | The primary dated ownership document: it states what was built, when, and with what evidence. | Free | Draft now, finalise after build |

**Explicitly not doing:** patent filing, a notarised declaration, or publishing the report publicly. None of these are needed for the contest, and each adds cost or risk without adding evidence.

---

## 7. Critical numbers

| Number | Value | Why it matters |
|---|---|---|
| Same-speaker voice match | **0.7306** | Two recordings of the same voice, measured with cosine similarity (a 0-to-1 score where 1 means identical voices). |
| Different-speaker voice match | **0.2964** | Two recordings of different voices, measured the same way. |
| Separation gap | **0.4342** | The distance between the two results. A wide gap means the comparison can tell voices apart on these samples. |
| Fingerprint size | **768 numbers** | Each voice fingerprint (embedding) is 768 decimal numbers. Small enough to store in a plain file. |
| Credit budget | **5,000 credits** | The allowance for Gnani API calls. Spend it on real feature tests, not on repeated experiments. |
| Credit usage page | `app.gnani.ai` → Usage | Where the remaining balance is checked. |
| Deadline | **10 November 2026** | Fixed. |

The measurement comes from `voiceprint_test.py`. Re-running it gives identical numbers, because the fingerprint step is deterministic (the same audio always produces the same numbers).

---

## 8. Known limitations

State these wherever the tool is described. They are not defects to hide; they are the boundary of what the evidence supports.

1. **A perfect clone of the enrolled voice passes Layer 1.** If the copy is clean and the words are ordinary, the fingerprint match will look like the real person. Matching an identity is not proof that the audio is genuine.
2. **A mismatch is not proof of a synthetic voice.** Layer 1 flags an identity mismatch. That catches cloned voices and also catches a human impersonator. It does not, on its own, show that the audio was machine-generated.
3. **The analysis runs on Gnani's cloud.** Audio leaves the machine, and the app stops working without an internet connection. It is a local interface with cloud inference.
4. **A partial search cannot prove absence.** "No scam patterns found" means the scan did not match its phrase list. It does not mean the call is safe, and the app must never say that it does.

---

## 9. Deferred and halted decisions

| Decision | Current state | Where it gets settled |
|---|---|---|
| UI/UX visual design | Halted. Waiting for real screens and real labels. | During build step 4 |
| Storage engine (plain text files vs a small local database) | Open. The default recommendation now lives in `05_DATA_MODEL.md` (JSON in `data\`). | During the build |
| README rewrite | Deferred. The current root `README.md` is a placeholder from the early API test. | After build, as the last documentation step |
| Contest pack (post, video script, submission answers) | Deferred. Writing it before the demo exists would mean rewriting it. | After build, build step 6 |

---

*Last updated: 4 November 2026. This is a living document: after the build finishes, re-read every section and correct anything that no longer matches the app.*
