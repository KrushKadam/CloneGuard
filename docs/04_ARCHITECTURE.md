# CloneGuard — Architecture & Technical Notes

**Prepared:** 4 November 2026

**Status:** Living document. Written before the build finishes, so some parts describe the plan rather than the shipped code. After the build, re-read every section and correct it against the app.

**Companion documents:** `docs/00_PROJECT_INDEX.md` (entry point, session rules, build order) · `docs/01_PRIOR_ART.md` (prior art, with sources) · `docs/02_POSITIONING.md` (canonical description, the 8-feature list, wording rules) · `docs/03_REQUIREMENTS.md` (acceptance criteria this design must satisfy) · `docs/05_DATA_MODEL.md` (what the app stores, field by field).

## 1. System overview

CloneGuard answers two questions about one call, then shows both answers side by side.

1. **Does the caller sound like the person they claim to be?** Layer 1 turns the caller's audio into a voiceprint (a long list of numbers that describes how a voice sounds, also called an embedding) and compares it with stored voiceprints of trusted people using cosine similarity (a 0-to-1 score where 1 means identical voices).
2. **Does the conversation use known scam language?** Layer 2 turns the audio into a transcript (the written text of what was said) using Prisma (Gnani's speech-to-text service) and scans that text for Hinglish (Hindi written in English letters, mixed with English) scam patterns.

The two results become one composite score (a single combined number) and one plain-language verdict. The screen always shows each layer's evidence separately, so a person can see why the score landed where it did.

```
 INPUTS                        ANALYSIS                                  OUTPUT
 ------                        --------                                  ------
 uploaded WAV  ---+--> Prisma STT --> transcript --> Layer 2 scan --+
 (from generator,  |                                                |
  disk, or the     +--> embeddings --> Layer 1 compare -------------+
  Self-Test)
                                        |
                          composite score + verdict rules
                                        |
              +-------------------------+-------------------------+
              |                         |                         |
        screen verdict          Timbre spoken verdict      incident log (JSON)
              |                                                   |
              +---------------------------------------------> PDF report (on demand)
```

The Self-Test Harness and the scam-call generator both feed the same INPUTS box. They are not separate products: they create audio and push it through the same pipeline a normal check uses. That is what makes the scorecard meaningful — the test path and the demo path are one path. Everything above the OUTPUT row runs on Gnani's cloud (remote servers reached over the internet through an API, a web service the app calls). The screen, the incident log, and the PDF (a document format that opens the same way on any machine) are local. Audio enters as a WAV (an uncompressed sound file), and Timbre (Gnani's text-to-speech service) speaks the verdict aloud.

## 2. Stack choices and why

| Choice | Chosen | Alternatives considered | Why this one |
|---|---|---|---|
| Interface | **Streamlit** (a Python library that turns a script into a web page) | Flask, Django, Electron, Android | A working local page with almost no layout code, in the same language as the existing Gnani helpers. Flask needs templates, routes, and session plumbing for the same result. Electron and Android are the wrong shape for a desktop tool with a week left. |
| Language | **Python 3** | Node, Go | `gnani.py` and `voiceprint.py` already work. Rewriting them buys nothing. |
| Audio and numbers | `wave`, `struct`, `math`, `requests` | NumPy, SciPy, librosa | The 768-number vectors are small; pure Python cosine runs in milliseconds. Fewer dependencies means fewer install failures on demo day. |
| Storage | **JSON files in a `data\` folder** (JSON is a plain text format of labelled values) | SQLite (a small single-file database), Postgres | One user, tens of records, no concurrent writers. Readable, easy to compare line by line in git, backed up by copying a folder, no server to start. **Default, changeable during build** — see `05_DATA_MODEL.md`, Section 1. |
| PDF | ReportLab or fpdf2 | Browser print-to-PDF, LaTeX | Keeps report generation inside the same script; browser printing needs a browser and manual steps. |
| Hosting | **Local host, no deployment** (served at `http://localhost:8501`) | Cloud deploy, Docker | The contest needs a working demo, not an operated service. Local hosting removes login, hosting cost, and data-handling questions. |

**In one sentence:** the tool is a thin local screen over three cloud calls, so the smallest stack that can call three web services and draw a table wins.

## 3. Gnani API reference

This section is the single source of truth. If code and this table disagree, this table is right and the code gets fixed.

**Base URL:** `https://api.vachana.ai`
**Auth:** the key lives in the environment variable `GNANI_API_KEY` (a named setting stored by the operating system, outside the code) and is sent as the header `X-API-Key-ID` on every call. It never appears in a file, a log, or a screenshot.

| Service | Purpose | Method and path | Body format | Key response fields |
|---|---|---|---|---|
| **Voice-Clone embeddings** | Audio → voiceprint | `POST /api/v1/tts/voice-clone/embeddings` | `multipart/form-data` (a file upload form), field `audio_file` | `data.voice_clone_embedding.embedding` — a base64 string (base64 packs binary data as plain text characters) that decodes to **768 little-endian float32** values (32-bit decimal numbers) |
| **Timbre TTS** (text-to-speech: written text becomes audio) | Text → speech | `POST /api/v1/tts/inference` | JSON: `text`, `voice`, `model`, `language`, `audio_config` | Raw WAV bytes |
| **Prisma STT** (speech-to-text: audio becomes text) | Audio → transcript | `POST /stt/v3` | `multipart/form-data`: `audio_file`, `model`, `language_code` | `transcript` (string) |

| Fixed value | Setting |
|---|---|
| Timbre model | `timbre-v2.5` |
| Timbre voices used here | `Nalini`, `Deepak` (a list of 766 voices exists) |
| Timbre language and audio | `hi-IN`; `sample_rate` 48000, `num_channels` 1, `sample_width` 2, `encoding` `linear_pcm`, `container` `wav` |
| Prisma model and language | `prisma-v3.0`; `indic-auto` (handles code-mixed Hindi/English without being told which language to expect) |
| Embedding size | 768 numbers |
| Credit budget | 5,000 credits (the unit Gnani bills API usage in); balance at `app.gnani.ai` → Usage |

**Quirk 1 — the label is wrong.** The API documentation calls the embedding `bfloat16` (a 16-bit number format). The bytes actually decode as **float32**. `voiceprint.py` handles both, but a parser written from the docs will produce garbage. Decode as float32.

**Quirk 2 — the vectors are not unit-normalized.** Their length (the norm, the straight-line size of the vector) is about **1.98**, not 1.0. That is fine as long as the comparison divides by both lengths, which is what cosine similarity does. The `cosine()` helper already does this. Do not "fix" it by assuming unit vectors.

**Practical implications.**

- **Every call costs credits.** One check is normally three calls: Prisma, embeddings, Timbre. A ten-scenario self-test is roughly twenty to thirty calls.
- **Cache embeddings.** The step is deterministic (the same audio always gives the same numbers), so store the vector with the enrolled voiceprint and reuse it.
- **Cache generated audio.** Generate a scenario WAV once; regenerating it for every run drains the budget for no gain.
- **Fail loudly.** A 401 means a bad key; a 404 or 405 means a wrong path. Both surface as readable errors, never as an empty result that looks like a pass.

## 4. Data flow, main action

One check, step by step. The steps match the diagram in Section 1.

1. **Audio arrives.** Uploaded WAV, or a generated scenario from `samples\`. The app checks the file exists, is non-empty, and is readable audio. A bad file is rejected here, before any credit is spent.
2. **Transcript (Prisma).** Audio posted to `/stt/v3` with `model=prisma-v3.0` and `language_code=indic-auto`; the returned `transcript` is stored with the check.
3. **Layer 2 scan.** The transcript is lowercased and scanned against the pattern list. Each match records category, matched phrase, surrounding snippet, and severity. Hits are a list, not a boolean.
4. **Voiceprint (embeddings).** The same audio goes to the embeddings endpoint; the base64 payload decodes to 768 float32 numbers and is cached against the audio path.
5. **Layer 1 compare.** The caller's vector is compared with each relevant enrolled voiceprint using `cosine()`. Every comparison is recorded: voiceprint id, name, score, threshold (the cut-off where a call flips from match to mismatch), pass or fail.
6. **Claimed identity adjusts the target.** A claim phrase ("Main Papa bol raha hoon", "CEO bol raha hoon") resolves to an enrolled person, and that person's voiceprint becomes the primary comparison. A claim naming nobody enrolled is reported, and the app falls back to the default voiceprint.
7. **Composite score.** Each layer's risk becomes a 0-to-1 number, then the two combine with fixed weights (Section 7). Simple arithmetic, written down here, not learned from data.
8. **Verdict rules.** The composite maps to one of three bands, and the band plus layer detail produces a plain-language sentence. A Layer 1 mismatch never produces the word "synthetic" on its own.
9. **Spoken verdict.** The sentence goes to Timbre and plays back. If that call fails, the text verdict stays and an error appears beside the play button.
10. **Incident log write.** The record is appended to `data\incidents.json` before the PDF step, so a report failure cannot lose the check.
11. **PDF on demand.** On export, the stored record renders to PDF and the path is written back.

**Initial threshold (tune during build):** identity match at **cosine ≥ 0.55**. The proven numbers are same-speaker **0.7306** and different-speaker **0.2964**, a gap of **0.4342**; 0.55 sits inside that gap, nearer the middle than either end. This is an **initial value, not a measured optimum**. The Self-Test Harness exists to move it.

## 5. Layer 1 design

**What it measures.** How close the caller's voiceprint is to a stored voiceprint. Nothing more. It does not inspect the audio for synthesis artefacts, and it cannot tell a perfect clone from the real person.

**Enrollment.** A WAV of a trusted person (or a generated one, since there is no microphone) goes through `get_embedding()` to 768 numbers. Those numbers are stored with a name, a role label ("Papa", "CEO"), a timestamp, and the source path. Re-enrolling the same role replaces the record by id rather than adding a duplicate.

**Matching.** `cosine(a, b)` returns a value from -1 to 1 in theory; in practice these embeddings land between roughly 0.2 and 0.8. It is shown as a 0-to-1 similarity with 1 meaning identical voices, rounded to four decimals so the log and PDF agree.

**Multi-voiceprint comparison.** Every check compares against the target voiceprint, and optionally against the others for context. The table shows all comparisons with the target row marked. A caller who matches nobody is a different signal from a caller who matches a different enrolled person.

**Claimed-identity detection.** A small resolver scans the transcript for claim patterns. It is a lookup over role labels and phrase variants, not a language model.

| Claim phrase (variant) | Resolves to |
|---|---|
| "main papa bol raha hoon", "papa bol raha hoon", "papa here" | enrolled voice with role "Papa" |
| "main mummy bol raha hoon", "mummy bol rahi hoon" | enrolled voice with role "Mummy" |
| "ceo bol raha hoon", "main ceo", "boss bol raha hoon" | enrolled voice with role "CEO" |
| "beta main hoon", "main tumhara papa" | enrolled voice with role "Papa" |

It returns the detected phrase, the resolved voiceprint id, and a resolution note ("exact role label", "alias", "no match"). When nothing resolves, the screen says "no claim detected — comparing against the default voiceprint". `03_REQUIREMENTS.md`, Feature 1 requires that sentence.

**Threshold policy.** One configurable number, default 0.55, always shown next to the score in the UI and the PDF. Changing it is a config edit, and the scorecard reports results at the current setting plus a small sweep around it.

**Tuning loop.** Enroll → generate scenarios → run the battery → read the scorecard → move the threshold → re-run. The loop is short because a threshold nobody can re-test is a guess.

## 6. Layer 2 design

**What it does.** Scans the transcript for language that shows up in Hinglish scam calls. It is a phrase matcher with severities, not a model that "understands" fraud. Output is a list of hits, each with a category, the matched phrase, and a snippet.

| Category | What it looks like | Example variants | Severity |
|---|---|---|---|
| Urgency and time pressure | A deadline forcing a fast decision | "abhi karna hoga", "sirf 10 minute", "turant", "aaj hi", "last chance" | medium |
| OTP, bank, or card details | Asks for a secret or an account number | "OTP bata do" (OTP is a one-time password), "CVV batao", "account number", "PIN share karo", "card details" | high |
| Authority impersonation | Claims to be someone whose word is obeyed | "main CEO bol raha hoon", "police se bol raha hoon", "bank manager", "government officer" | high |
| Threats and consequences | Threatens loss, arrest, or exposure | "account block ho jayega", "police case", "legal action", "warrant", "paise kat jayenge" | high |
| Emotional manipulation | Uses fear, family, or sympathy | "papa bimar hain", "mujhe bachao", "kisi ko mat batao", "please help" | medium |
| Deceptive call to action | Pushes a payment, transfer, or install | "google pay se bhejo", "UPI karo", "link kholo", "team viewer install karo", "anydesk" | high |

**Where patterns live.** `data\patterns.json`, one record per pattern: id, category, phrase variants, severity, weight. Editing the file changes behaviour without touching code, so the phrase list can grow during the build and stay reviewable. Patterns are dual-script: Prisma STT returns Devanagari, so each phrase has Latin + Devanagari variants (32 patterns, ~204 variants).

**Matching rules.**

- Lowercase, collapse whitespace, and strip punctuation before matching. The stored snippet keeps the original text.
- Substring match per variant. Hinglish has many spellings, so each pattern carries variants instead of one exact string.
- One hit per pattern per check, even if the phrase repeats; the score counts the pattern once.
- Overlapping patterns may co-fire (an authority claim and an OTP request can both hit). That is realistic.

**Recording.** Each hit stores `category`, `matched_phrase`, `transcript_snippet` (about 80 characters either side), `severity`, `weight`. The UI and PDF show this table, because "Layer 2 flagged something" with no phrase is not evidence.

**What it cannot do.** The list covers known phrasings. A scam that avoids every variant scores zero on Layer 2, and the app must not read that as safety. The verdict says "no patterns matched", never "safe".

## 7. Composite score

The score is arithmetic with fixed weights. It is not trained, not learned, not a model. Anyone can recompute it by hand from the stored record, which is the point.

| Input | Where it comes from | Range |
|---|---|---|
| `best_cosine` | Highest Layer 1 score against the target voiceprint | 0 to 1 |
| `threshold` | Config value, default 0.55 | 0 to 1 |
| `layer2_hits` | Layer 2 hit list, each with a `weight` | 0 to many |

**Step 1 — Layer 1 risk.** `layer1_risk = clamp((threshold - best_cosine) / threshold, 0, 1)`, where clamp keeps the result between 0 and 1. At or above the threshold the risk is 0; at a cosine of 0 it is 1. A cosine of 0.40 against 0.55 gives about 0.27.

**Step 2 — Layer 2 risk.** `layer2_risk = min(1, sum(weights) / 0.8)`. Two high-severity hits at 0.4 each reach 1.0; one medium hit at 0.2 gives 0.25.

**Step 3 — Combine.** `composite = round(100 * (0.5 * layer1_risk + 0.5 * layer2_risk))`. Equal weights are a starting choice: neither layer is trusted more until the self-test shows which one earns it.

**Step 4 — Verdict bands.**

| Composite | Band | Plain sentence |
|---|---|---|
| 0–29 | Low risk | "The caller's voice is consistent with the enrolled person and no scam patterns matched. This is a weak signal, not a clearance." |
| 30–59 | Caution | "One layer raised a concern. Ask a verification question the real person would answer." |
| 60–100 | High risk | "The caller does not match the claimed person's voice, or the conversation uses known scam patterns, or both. Treat this call as unsafe." |

**Special case — no comparable voiceprint.** If the claim names someone not enrolled, Layer 1 is marked "not comparable" and the composite uses Layer 2 alone, rescaled to 0–100, with the screen saying so. Scoring a missing comparison as zero would make an unknown caller look safe.

**Explainability rule.** The composite never appears without the two layer panels beside it, each with its own numbers, threshold, and evidence. A verdict that cannot be traced to a phrase and a cosine value is a bug.

## 8. Self-Test Harness design

One button runs the tool against a battery of calls whose answers are already known, then prints a report card comparing decisions with truth.

| Part | Contents | Ground truth |
|---|---|---|
| Scam set | Scenarios across the six Layer 2 categories, voiced by someone other than the enrolled person but claiming to be them | `type = scam` |
| Genuine set | Ordinary conversations in the enrolled person's own voice, no scam phrases | `type = genuine` |
| Hard cases | A genuine call that mentions money; a scam call with no urgency words; a near-threshold voice match | Label recorded with the scenario |

**Run mechanics.** Read `data\scenarios.json`; run each scenario through the same pipeline a manual check uses (STT → Layer 2 → embeddings → Layer 1 → composite → verdict); compare the band with `expected_label`. A scam counts as caught at High risk, a genuine call counts as passed at Low risk. Caution counts as a miss in both directions and is reported separately, because a hedge is not a correct answer. A failed API call marks the scenario `error`, never `caught` or `passed`. The run is written to `data\selftest_runs.json`.

| Metric | Meaning |
|---|---|
| Scam caught X/Y | High-risk verdicts on scam scenarios, over the scam total |
| Genuine passed N/M | Low-risk verdicts on genuine scenarios, over the genuine total |
| Caution count | Scenarios that landed in the middle band |
| Errors | Scenarios that did not complete |
| Weakest scenario | The scenario furthest from its expected band, named with its score |
| Threshold sweep | The same results recomputed at a few thresholds around the current one, so sensitivity is visible |

**PDF export.** A one-page PDF: run id, date, scenario count, the metrics above, a per-scenario table, and the threshold sweep.

**What a good scorecard proves.** That decisions were checked against known answers, that failures are visible, and that the threshold was chosen with evidence. It does not prove real-world accuracy: the scripts come from the same person who wrote the patterns, so the test is honest about calibration (how closely the tool's decisions line up with known answers) but not independent of the builder. Calibration outcome: scam caught 7/7, genuine passed 3/3, caution 0, errors 0, flat across thresholds 0.45-0.65; test scripts and patterns were both written by the builder (not imported).

## 9. Scam-call generator design

The machine has no microphone, so every test file is made, not recorded. One Hinglish script template per pattern category, written to sound like a real call rather than a translated form letter. Each template has slots — claimed relationship, amount, deadline, payment method — filled from a small fixed list so output stays reviewable.

| Template family | Claim | Pressure device |
|---|---|---|
| Family emergency | "Main Papa bol raha hoon" | accident, hospital, urgent money |
| Bank fraud desk | "Bank se bol raha hoon" | account block, OTP, card details |
| Executive request | "Main CEO bol raha hoon" | confidential transfer, secrecy |
| Government or police | "Police station se" | case, warrant, fine |
| Tech support | "Company se technical team" | remote access, screen share |
| Prize or refund | "Aapka refund pending hai" | link, fee, account number |

**Voice assignment.** Timbre `Nalini` or `Deepak` for the caller, chosen so the caller differs from the enrolled voice in scam scenarios. Genuine scenarios use the same voice as the enrolled person — that is the point of a control.

**Audio shaping.** Generate at 48 kHz mono, then apply a light phone-line effect (band-limit plus low noise) with `wave` and `struct`. Closer to a call than studio speech. It is simulated noise, not a real carrier channel, and the docs say so.

**Output.** A WAV in `samples\`, plus a scenario record in `data\scenarios.json` with `category`, `type`, `script_text`, `timbre_voice`, `audio_path`, `expected_label`, `created_at`.

## 10. Spoken verdict

Timbre reads the verdict sentence aloud. The spoken text is the same text shown on screen, not a shortened version — divergence between what is read and what is displayed is a trust bug. It names both layers in plain words: "Voice match is low: the caller does not sound like Papa. The call also asked for an OTP. Overall risk is high. Do not share codes or send money." The voice is selectable (`Nalini` or `Deepak`), defaulting to the configured voice. Audio goes to a temp file and plays in the Streamlit audio widget; it is not added to the incident record unless the user saves it. A failed speech call shows "spoken verdict unavailable" and leaves the text untouched.

## 11. PDF report design

One PDF per check, generated on demand from the stored record.

| Section | Contents |
|---|---|
| Header | "CloneGuard evidence report", check id, timestamp, app version |
| Caller audio | File name, duration, sample rate, generated or uploaded |
| Layer 1 evidence | Table: voiceprint name and role, cosine, threshold, pass or fail; target row marked |
| Claimed identity | Detected phrase and resolved voiceprint, or "no claim detected" |
| Layer 2 evidence | Table: category, matched phrase, transcript snippet, severity |
| Composite | Layer 1 risk, Layer 2 risk, weights, composite score, band |
| Verdict | The plain-language sentence, identical to the screen |
| Limitations | The four limitations from Section 15, in short form, including that a mismatch is not proof of synthetic audio |
| Footer | Generated date, "local interface, cloud inference via Gnani", page number |

Styling stays plain: one accent colour, a readable sans-serif (plain lettering without the small decorative strokes), tables that fit A4 width. Evidence PDFs use Nirmala font (`C:\Windows\Fonts\Nirmala.ttc`) with uharfbuzz shaping for native Devanagari. No logo work before the pipeline works.

## 12. Folder structure

As-built layout after the build.

```
gnani-voice-app\
├── app.py
├── config.py
├── gnani.py
├── voiceprint.py
├── engine\                 layer1.py, layer2.py, claim.py, score.py, pipeline.py, __init__.py
├── generator\              scripts.py (Hinglish templates), generate.py (TTS + phone effect), __init__.py
├── selftest\               harness.py (battery runner), scorecard.py (metrics + PDF), __init__.py, scorecard_pdfs\
├── reports\                incident_pdf.py, __init__.py, out\ (generated PDFs)
├── data\                   voiceprints.json, incidents.json, scenarios.json,
│                           selftest_runs.json, patterns.json, embedding_cache.json, stt_cache.json
├── samples\                13 generated WAVs + embeddings.json
├── docs\                   this document set
└── README.md
```

## 13. Error handling

The rule: a failure is a message on screen, never a crash and never a silent pass.

| Situation | What the user sees | What the app does |
|---|---|---|
| No internet | "Cannot reach Gnani. Check your connection and try again." | Catches the connection error, keeps the page alive, leaves prior results intact |
| API returns 401 | "API key rejected. Check `GNANI_API_KEY`." | Stops the check, no retry loop |
| API returns 5xx, or times out | "Gnani had a problem (code 500). Try again in a moment." / "The request took too long and was stopped." | Shows the code, offers retry; timeout at 60–120 s, no partial result written |
| Credits low or exhausted | Pre-run estimate ("this run will use about N credits"), then "Credit limit reached — check app.gnani.ai → Usage." | Battery stops and reports which scenarios completed |
| Missing `GNANI_API_KEY` | "Set the environment variable `GNANI_API_KEY` and restart the app." | Checked at startup and before each call |
| Empty or corrupt audio | "That file is empty or not readable audio. Upload a WAV." | Validates size and header before spending a credit |
| No voiceprint enrolled | "Enroll a voice before running a check." | Disables the check button |
| Self-test scenario errors | Row marked `error`, counted separately | Never counted as caught or passed |
| PDF write fails | "Report could not be saved. The check is still in the incident log." | Log write happens before PDF, so nothing is lost |

## 14. Configuration

Settings live in `config.py` as named constants, optionally readable from `config.json` if editing without a restart is needed.

| Setting | Default | Note |
|---|---|---|
| `APP_VERSION` | `"0.1.0"` | Shown in UI header and PDF footer |
| `THRESHOLD` | 0.55 | Layer 1 identity match cutoff; tune with Self-Test Harness |
| `W_L1` / `W_L2` | 0.5 / 0.5 | Composite score weights; equal until scorecard argues otherwise |
| `LAYER2_DIVISOR` | 0.8 | Sum of Layer 2 hit weights that saturates Layer 2 risk at 1.0 |
| `BAND_CUTOFFS` | `(30, 60)` | Composite bands: [0,30) low, [30,60) caution, [60,100] high |
| `STT_MODEL` / `LANGUAGE_CODE` | `prisma-v3.0` / `indic-auto` | Prisma STT model and language |
| `TIMBRE_MODEL` / `TIMBRE_VOICE_DEFAULT` | `timbre-v2.5` / `Nalini` | `TIMBRE_VOICES` = `["Nalini", "Deepak"]` |
| `EMBEDDING_DIM` | 768 | Sanity check on every parsed vector |
| `DATA_DIR` / `SAMPLES_DIR` | `data\` / `samples\` | JSON collections, generated WAVs |
| `PATTERNS_PATH` | `data\patterns.json` | Editable phrase list |
| `VOICEPRINTS_PATH` / `INCIDENTS_PATH` | `data\voiceprints.json` / `data\incidents.json` | Enrolled voices, incident log |
| `EMBEDDING_CACHE_PATH` / `STT_CACHE_PATH` | `data\embedding_cache.json` / `data\stt_cache.json` | Local caches, re-running a check never re-bills |
| `DEFAULT_VOICEPRINT_ID` | `None` | Fallback voiceprint; `None` = first enrolled record |

**The API key is never a config value.** It stays in `GNANI_API_KEY`, read at call time. Nothing in `config.py`, `data\`, or the repo contains it, and `.gitignore` covers WAV outputs and any local secrets file.

## 15. Privacy and safety

**Where data goes.** Audio and logs stay on the machine, with one exception: the audio needed for analysis goes to Gnani's cloud for transcription and embedding, and verdict text goes for speech. Nothing else leaves. There is no account system, no analytics, and no telemetry.

**What the tool claims.** Four limits, stated in the UI, the PDF, and every public description:

1. **A perfect clone of the enrolled voice passes Layer 1.** Matching an identity is not proof that the audio is genuine.
2. **A voiceprint mismatch is an identity-risk indicator, not proof that the audio is synthetic.** It flags a mismatch between the caller and the enrolled voice, which catches clones and human impersonators alike.
3. **Gnani inference is cloud-hosted.** The app needs an internet connection, and audio leaves the machine for analysis.
4. **A partial search cannot prove absence.** "No patterns found" means the phrase list did not match. It does not mean the call is safe.

**What it is for.** A risk signal with visible evidence, for a human to weigh. It does not prove a crime, does not replace verification, and does not decide on its own. Demo audio is generated: no real victim recording and no real scam call without consent.

## 16. Open decisions (halted — decide during build)

| Decision | State | Settled by |
|---|---|---|
| Screen layout and tab names | Halted | Build step 4, once real labels exist |
| Final storage engine | Default JSON, changeable | Revisit if a query needs joins or the log passes a few thousand rows |
| Exact threshold | **RESOLVED** — 0.55 kept (sweep flat 0.45–0.65) | Self-Test scorecard sweep |
| Pattern list contents | Six categories seeded | Add variants as generated scripts reveal gaps |
| Layer 1 also comparing non-target voiceprints by default | Leaning yes, for context | Demo readability |
| PDF styling and page count | Plain, one to two pages | Build step 5 |
| Phone-line effect strength | Light band-limit plus noise | Listen to a sample before the demo |
| Layer weights | **RESOLVED** — stayed 0.5/0.5 (pattern growth earned the result, no weight change) | Self-Test scorecard sweep |

---

*Last updated: 4 November 2026. This is a living document: after the build, re-read each section against the code and correct every path, threshold, and number that no longer matches.*
