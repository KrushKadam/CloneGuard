# CloneGuard — Positioning & Language Rules

**Prepared:** 4 November 2026  
**Use for:** submission text, README, demo narration, LinkedIn posts, judge Q&A.  
**Companion document:** `docs/01_PRIOR_ART.md` — the evidence base for every prior-art statement here.

---

## 1. Positioning statement

Use this paragraph unchanged. It is the canonical description of the project.

> CloneGuard is a working, tested desktop tool that checks whether a caller's voice matches a trusted enrolled person, and scans the conversation for Hinglish scam patterns — built entirely on Gnani voice APIs. The problem is validated at national scale (AICTE SIH26104; Pindrop/Resemble enterprise markets). The field is crowded with prototypes and enterprise products; CloneGuard's contribution is a complete, measurable, explainable implementation: proven voiceprint separation (0.7306 vs 0.2964), a self-contained Hinglish scam-call generator for testing, a Self-Test Harness that attacks the tool and issues a calibration scorecard, two-layer evidence reporting, and PDF incident reports — free to run, local interface with cloud inference via Gnani.

### 1.1 What each clause is doing

| Clause | Evidence behind it | What not to add |
|---|---|---|
| "working, tested desktop tool" | The voiceprint experiment is measured; the app runs through Gnani APIs. | Do not say "production-ready" or "enterprise-grade." |
| "checks whether a caller's voice matches a trusted enrolled person" | Layer 1 cosine comparison (a 0-to-1 score where 1 means identical voices) against an enrolled voiceprint. | Do not say it "detects AI clones" as a fact. |
| "scans the conversation for Hinglish scam patterns" | Layer 2 transcript rules over Prisma output (Gnani's speech-to-text service turns audio into text). | Do not say it "understands" fraud intent. |
| "built entirely on Gnani voice APIs" | Voice-Clone embeddings (voice fingerprints), Prisma, and Timbre (Gnani's text-to-speech service). | Do not imply Gnani endorses the project. |
| "problem is validated at national scale" | AICTE SIH26104; Pindrop and Resemble sell into this market. | Do not say the problem was previously ignored. |
| "field is crowded" | See `01_PRIOR_ART.md`, Sections 2–5. | Do not soften this into a claim of empty space. |
| "proven voiceprint separation (0.7306 vs 0.2964)" | Same-speaker cosine 0.7306; different-speaker 0.2964; gap 0.4342. | Do not present this as a benchmark win or a certified evaluation. |
| "Self-Test Harness that attacks the tool" | The tool generates scam and genuine calls and runs them through the pipeline. | Do not call the scorecard "accuracy" without stating the test set. |
| "free to run" | No licence fee for the app. | Do not imply Gnani API usage is unmetered. |
| "local interface with cloud inference" | Streamlit (a Python library that turns a script into a web page) runs locally; Gnani inference is remote. | Do not shorten this to "offline" or "on-device." |

---

## 2. Wording rules

These rules apply to every public sentence: UI labels, README, demo script, submission form, social posts, and answers to judges.

| Do not say | Say instead |
|---|---|
| offline / fully on-device | local desktop interface, cloud inference via Gnani APIs |
| "detects AI-cloned voice" (as fact) | "flags identity mismatch between caller and enrolled voice" — this catches clones **and** human impersonators |
| exclusivity or novelty superlatives (originality, sole-provider, absence-of-precedent framing) | feature-level descriptions with sources |
| "Hinglish fraud is an unoccupied field" | "Hinglish is our tested focus; the problem is nationally validated by AICTE SIH26104" |
| "proves a voice is fake" | "identity risk signal plus scam-pattern evidence; the verdict shows both layers" |

### 2.1 Additional rules

| Do not say | Say instead |
|---|---|
| "100% accurate" / "guaranteed detection" | "measured on N calls in the Self-Test Harness; see the scorecard" |
| "replaces human verification" | "adds a risk signal; a human makes the final decision" |
| "real-time live call interception" | "analyses audio supplied to the app" (unless a streaming integration is actually running) |
| "AI detector" | "identity and language risk check" |
| "military-grade" / "bank-level security" | describe what is actually implemented: local UI, API key from environment, PDF evidence |

### 2.2 Why these rules exist

Each banned phrasing claims something the tool cannot support:

- "Offline" is false: Gnani inference is cloud-hosted.
- "Detects AI cloning" overstates Layer 1: a voiceprint mismatch also catches a human impersonator, and a clean clone of the enrolled voice can pass.
- Superlatives invite a prior-art challenge that the project does not need. The demo is stronger than the adjective.
- "Unoccupied field" is an absence claim from a partial search.

---

## 3. Final feature list

Eight features. This is the list to use in the submission and the demo. Do not add features that are not demonstrated.

| # | Feature | What it does | Evidence or output |
|---:|---|---|---|
| 1 | **Multi-voiceprint enrollment with claimed-identity detection** | Stores several trusted voiceprints (for example, family members or executives). When the transcript contains a claim such as "Main Papa bol raha hoon" or "CEO bol raha hoon," the app checks that person's voiceprint instead of a generic one. | Enrolled-voice list; detected claim; matched voiceprint ID |
| 2 | **Two-layer verification with composite score** | Layer 1 computes cosine similarity against the enrolled voiceprint. Layer 2 scans the Prisma transcript for Hinglish red flags (urgency, secrecy, payment requests, OTP, authority claims, remote-access instructions). The verdict shows both layers and a composite score. | Layer scores, matched red-flag phrases, composite score, evidence breakdown |
| 3 | **Built-in Hinglish scam-call generator** | Produces scam and genuine call scripts with Timbre voices and a phone-line noise effect, so the demo does not depend on external recordings. | Generated WAV files with known ground truth (scam or genuine) |
| 4 | **Self-Test Harness** | Runs a one-click adversarial battery of scam and genuine scenarios through the full pipeline, then prints a calibration scorecard: scam caught X/Y, genuine passed A/B, weakest scenario, and threshold behavior. Exports the scorecard as a PDF. | Calibration scorecard plus PDF |
| 5 | **Spoken verdict via Timbre** | Speaks the result aloud, so the verdict works in a hands-free or demo setting. | Audio verdict in the selected voice |
| 6 | **Incident log** | Keeps a local record of checks: timestamp, claimed identity, layer scores, verdict, and transcript excerpt. | Incident history in the app |
| 7 | **PDF evidence report per check** | Exports a shareable report with the two layer scores, red-flag evidence, transcript excerpt, and verdict. | One PDF per check |
| 8 | **Streamlit UI at localhost** | Local desktop interface, cloud Gnani inference. Enrollment, checking, generation, self-test, and reports live in one app. | App running at `localhost` |

### 3.1 Evidence status

The measured number available in the repository is the voiceprint cosine similarity gap: same-speaker **0.7306**, different-speaker **0.2964**, gap **0.4342** (from `voiceprint_test.py`). Layer 1 is plain cosine comparison of embeddings — no dedicated voice-analysis/separation model was shipped. The Self-Test Harness is the mechanism that produces the rest of the evidence at demo time: it generates the calls, runs them, and reports the calibration.

Do not quote a detection accuracy that has not been produced by a completed harness run. Quote the scorecard instead.

### 3.2 The 60-second demo path

| Time | Action | What the viewer sees |
|---:|---|---|
| 0–10 s | Enroll a trusted voice, then generate a scam call in a different voice claiming to be that person | Enrollment and generator in one screen |
| 10–25 s | Run the check | Layer 1 mismatch, Layer 2 red flags, composite verdict |
| 25–40 s | Run the Self-Test Harness | Scorecard: scam caught, genuine passed, weakest scenario |
| 40–50 s | Play the spoken verdict | Timbre voice states the result |
| 50–60 s | Open the PDF report and incident log | Evidence artifact the viewer can keep |

---

## 4. Award mapping

Use this table to choose what to show for each criterion. The "supporting fact" column is deliberately sourced; the "caution" column prevents overclaiming.

| Criterion | What to show | Supporting fact | Caution |
|---|---|---|---|
| **Real-world impact** | A fraud check that a person or small team can run without an enterprise contract. | Pindrop reports a 1680% spike in AI attacks (vendor analysis, autumn 2024–spring 2026). Resemble's H1 2026 report logs 821 verified deepfake attacks from 1,760 news reports. | Both figures are vendor-reported. The 821 count covers all deepfake media, not voice alone. Attribute the source and the scope. |
| **Creativity** | The Self-Test Harness: the tool generates attacks against itself and publishes a calibration scorecard. | The generator and the checker share one pipeline, so the test is reproducible in the demo. | It is adversarial self-testing against known scripts, not an independent red-team. |
| **Hinglish / code-mixed** | Scam scripts and transcript rules written for Hinglish, not translated from English. | SIH26104 explicitly asks for multilingual Indian contexts. | Do not claim Hinglish fraud is unaddressed elsewhere; claim it as the tested focus. |
| **Noisy telephonic audio** | The generator applies a phone-line noise effect; the demo uses call-like audio rather than studio recordings. | The pipeline is exercised on degraded audio, which is closer to a real call than clean TTS. | This is simulated phone noise, not a real carrier channel. |
| **Solo project award** | State the scope plainly: one builder, three Gnani APIs, one end-to-end flow. | Present the build as solo work; the demo shows the scope. | Do not inflate scope by listing features that are not demonstrated. |
| **60-second demo award** | The self-contained path in Section 3.2: enroll, generate, check, self-test, speak, export. | No external recording or second service is needed beyond Gnani. | Rehearse the API latency; have a pre-generated fallback if the network stalls. |
| **Crowd favourite** | Play a short synthetic scam call, then show the verdict. | Scam content is immediately understandable to a non-technical audience. | Use synthetic demo clips. Do not use a real victim's audio or a real scam recording without consent. |

### 4.1 Presenting the impact numbers

Use this sentence pattern:

> "Pindrop, a vendor in this market, reports a 1680% rise in AI attacks in its own fraud data. Resemble's H1 2026 report counts 821 verified deepfake attacks across media. Those are vendor figures, and they show why identity checks on calls matter."

Do not say "voice cloning is up 1680%." The Pindrop figure is broader than voice cloning, and it is not an independent statistic.

---

## 5. Narrative hooks

These are for later LinkedIn posts and the submission. Use them as written, with the notes that follow.

> **Hook 1 — national validation:**  
> "AICTE made voice-clone impersonation a national hackathon problem (SIH26104) — this is my working solution built on Gnani voice APIs."

> **Hook 2 — access:**  
> "Enterprise tools like Pindrop sell this to banks; CloneGuard runs free on your laptop."

> **Hook 3 — self-test:**  
> "I built a fraud detector, then made it attack itself and publish its own report card."

### 5.1 Notes for using the hooks

- **Hook 1:** link to the SIH26104 problem statement. Say "working solution" if and when the demo path in Section 3.2 runs end to end on the day.
- **Hook 2:** the phrase "runs free on your laptop" must be followed in the same post by "local interface, cloud inference via Gnani." Otherwise it implies offline processing. "Free" refers to the app, not to Gnani API usage.
- **Hook 3:** pair it with a screenshot of the scorecard. The line is memorable; the artifact makes it credible.

### 5.2 Tone

Plain, specific, and calm. Lead with the problem and the demo, not with adjectives. When a judge asks "hasn't this been done?", answer with the prior-art document, then show the self-test scorecard. Do not argue that the idea is new; argue that this implementation is complete and measurable.

---

## 6. What we do not claim

- **Not an invention.** Voiceprint verification, synthetic-speech detection, and scam-text analysis all have prior art. See `docs/01_PRIOR_ART.md`.
- **Not a research paper contribution.** No new model, dataset, or benchmark is claimed.
- **No uniqueness or superlative claims.** No originality, sole-provider, or absence-of-precedent framing.
- **Not proof of AI cloning.** Layer 1 flags identity mismatch. That catches clones and human impersonators. It does not prove a voice is synthetic.
- **Not offline or on-device.** The interface is local; Gnani inference is cloud-hosted, and audio leaves the machine for inference.
- **Not a replacement for human judgment.** The verdict is a risk signal with evidence, not an automatic fraud determination.
- **Not a certified biometric system.** The 0.7306-versus-0.2964 result is a small-sample measurement, not a forensic evaluation across devices and channels.
- **Not carrier-grade live interception.** The build analyses audio supplied to the app; telephony streaming and consent handling are out of scope.
- **Not validated on real scam calls at scale.** The Self-Test Harness uses generated scenarios with known ground truth.

---

## 7. Pre-publish checklist

Before submitting or posting, check every public sentence against this list:

- [ ] No banned framing: offline, on-device, "detects AI clone" as fact, superlatives, "proves fake."
- [ ] Every number has a source and a date.
- [ ] Vendor statistics are labelled as vendor-reported, with their scope.
- [ ] The phrase "local interface, cloud inference via Gnani" appears wherever "free" or "desktop" appears.
- [ ] The 0.7306 / 0.2964 result is described as a measured voiceprint separation, not an accuracy score.
- [ ] The Self-Test Harness result is quoted from a completed run, with the number of scenarios.
- [ ] The demo uses synthetic audio, not a real victim's recording.
- [ ] The prior-art document is linked wherever novelty could be implied.

---

*Positioning is a claim about execution, not about inventing the category. The evidence lives in `docs/01_PRIOR_ART.md`.*
