# CloneGuard — Data Model (What the App Stores)

**Prepared:** 4 November 2026

**Purpose:** the exact fields, types, and shapes the app writes. Follow this structure instead of inventing a new one, so the incident log, the PDF report, and the Self-Test scorecard all read from the same records.

**Status:** Living document. Written before the build finishes. After the build, correct every field name and path against the real files.

**Companion documents:**

- `docs/00_PROJECT_INDEX.md` — entry point, session rules, build order.
- `docs/02_POSITIONING.md` — the 8-feature list and wording rules.
- `docs/03_REQUIREMENTS.md` — acceptance criteria these records have to support.
- `docs/04_ARCHITECTURE.md` — the pipeline that produces these records.

---

## 1. Storage choice

**Default: JSON files in a `data\` folder.** JSON is a plain text file format of labelled values; a person can open it in Notepad and read it.

| Collection | File | Holds |
|---|---|---|
| Enrolled voiceprints | `data\voiceprints.json` | One record per trusted person |
| Incidents | `data\incidents.json` | One record per completed check |
| Self-test runs | `data\selftest_runs.json` | One record per battery run (keyed by run_id) |
| Scenarios | `data\scenarios.json` | One record per generated test call |
| Patterns | `data\patterns.json` | One record per scam-phrase rule |
| STT cache | `data\stt_cache.json` | Transcripts keyed by `path|size|mtime` |
| Embedding cache | `data\embedding_cache.json` | Embeddings keyed by `path|size|mtime` |

**Why JSON here.**

- One user, one machine, small numbers of records. A database server adds a process to start and a dependency to install, and buys nothing at this size.
- Human-readable. A judge, or future-me, can open the file and see what was stored without a tool.
- Easy to back up: copy the folder.
- Easy to compare line by line in git, which supports the dated ownership trail.
- No schema migration step when a field is added mid-build.

**Alternative: SQLite** (a small single-file database). Use it if the incident log grows past a few thousand rows, or if the UI needs filtered queries and joins across collections (a join is a lookup that combines records from two collections). The record shapes in Section 2 are written so they map to tables without redesign: each list becomes a child table with a parent id.

**Marked: default, changeable during build.** Switching engines is a code change in one storage module, not a rewrite of the pipeline, as long as nothing outside that module opens the files directly.

**Write rules.**

- Records are added, never edited. For incidents and self-test runs, a record does not change after the check completes.
- Write the incident before generating a PDF, so a report failure cannot lose the check.
- Write to a temp file, then rename, so a crash mid-write cannot leave half a JSON file.
- One list per file, no nested top-level objects.
- Caches (`stt_cache.json`, `embedding_cache.json`) are keyed by absolute path + file size + mtime (`path|size|mtime`); re-running on the same file costs 0 API credits.

---

## 2. Entities

Five record types. Every field below appears in the files exactly as named.

### 2.1 Enrolled voiceprint

A stored fingerprint of a trusted person's voice.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | Short identifying label, e.g. `vp_papa`. Used everywhere else to refer to this person. |
| `name` | string | The name shown in the app, e.g. "Nalini". |
| `role` | string | The role a caller might claim, e.g. "Papa", "CEO". The claimed-identity resolver matches against this. |
| `created_at` | string (ISO 8601) | When the voiceprint was enrolled, in a standard date-and-time text format, e.g. `2026-11-05T09:38:07+05:30`. |
| `embedding` | list of 768 numbers | The voice fingerprint itself. Stored as decimal numbers, not as base64, so it stays readable and comparable. |
| `source_path` | string | Where the enrollment WAV lives, e.g. `samples\A1_nalini_X.wav`. |

Rules: `role` is the lookup key for claims, so it must be short and consistent ("Papa", not "my father"). Re-enrolling the same `role` offers to replace the existing record rather than silently creating a duplicate.

### 2.2 Incident

One record per completed check. This is the record the incident log lists and the PDF report renders.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | Identifying check id, e.g. `inc_14bb8753a157`. |
| `checked_at` | string (ISO 8601) | When the check ran. |
| `created_at` | string (ISO 8601) | Same as `checked_at`; kept for consistency. |
| `audio_path` | string | The audio file that was analysed. |
| `transcript` | string | The full text Prisma (Gnani's speech-to-text service) returned. |
| `claim` | object | The claim that was detected: `detected_phrase` (string or null), `role` (string or null), `voiceprint_id` (string), `enrolled` (boolean), `note` (string). When no claim is found, `detected_phrase` and `role` are null and `note` explains the default comparison. |
| `layer1` | object | Contains `comparisons` (array), `target_id`, `best_cosine`, `threshold`, `label` ("identity match" / "mismatch" / "not comparable"), `comparable` (boolean). See below. |
| `layer2` | object | Contains `hits` (array of hit objects). See below. |
| `composite` | integer 0–100 | The combined risk number. |
| `band` | string | `low`, `caution`, or `high`. |
| `verdict_sentence` | string | The exact sentence sent to Timbre (Gnani's text-to-speech service), so the audio and the screen can be compared later. |
| `notes` | array of strings | Free-text notes about this call (e.g. why the default voiceprint was used). No `pdf_path` field — PDFs are generated on demand into `reports\out\`. |

**Layer 1 comparison object** (inside `layer1.comparisons[]`).

| Field | Type | Description |
|---|---|---|
| `voiceprint_id` | string | Which enrolled person was compared. |
| `name` | string | Copied in for readability, so the log survives a deleted voiceprint. |
| `role` | string | The role of that voiceprint. |
| `cosine` | number | The similarity score, 0 to 1, where 1 means identical voices, rounded to four decimals. |
| `threshold` | number | The cut-off in force at the time of the check. |
| `verdict` | string | `match` or `mismatch` (replaces boolean `passed`). |
| `target` | boolean | `true` for the voiceprint the claim pointed at, or the default when no claim was found. |

**Layer 2 hit object** (inside `layer2.hits[]`).

| Field | Type | Description |
|---|---|---|
| `category` | string | One of the six categories. |
| `matched_phrase` | string | The exact variant that fired. |
| `transcript_snippet` | string | About 80 characters either side of the match. |
| `severity` | string | `medium` or `high`. |
| `weight` | number | The pattern's contribution to the score (0.2 or 0.4). |

### 2.3 Self-test run

One record per battery run. Keyed by `run_id`; the latest run is `run_20261107_182914_fa8e` (scam 7/7, genuine 3/3, caution 0, errors 0).

| Field | Type | Plain-English description |
|---|---|---|
| `run_id` | string | e.g. `run_20261107_182914_fa8e`. |
| `started_at` | string (ISO 8601) | When the battery started. |
| `threshold` | number | The cosine threshold used for this run (e.g. 0.55). |
| `scenario_count` | integer | Number of scenarios attempted (always 10). |
| `metrics` | object | `scam_caught` ("7/7"), `genuine_passed` ("3/3"), `caution_count`, `errors`, `weakest`, `weakest_category`, `weakest_composite`, `weakest_distance`. |
| `scenarios` | list of result objects | One entry per scenario attempted. See below. |

No `scorecard_pdf_path` field in the run record — PDFs are generated on demand.

**Scenario result object** (inside `scenarios[]`).

| Field | Type | Description |
|---|---|---|
| `scenario_id` | string | Matches a scenario's `audio_path` stem, e.g. `sc01_family_emergency`. |
| `category` | string | The scam category, or `ordinary` for genuine calls. |
| `expected_label` | string | `scam` or `genuine`. |
| `hard_case` | string or null | Optional tag for difficult test cases. |
| `audio_path` | string | Path to the scenario WAV. |
| `composite` | integer | The composite score (0–100). |
| `band` | string | `low`, `caution`, or `high` (replaces `actual_verdict`). |
| `status` | string | `caught`, `missed`, or `error` (replaces boolean `caught`). |
| `distance` | integer | Points from the nearest band boundary (0 = on boundary). |
| `best_cosine` | number | Highest cosine from Layer 1 for this scenario. |
| `hits` | array | Layer 2 hit objects (same structure as `incidents.layer2.hits`). |
| `error` | string or null | Error message if the scenario failed. |

Errors are recorded as `status = "error"` with `error` populated. They are never folded into the caught or passed counts.

### 2.4 Scenario (generated test call)

A single generated call with a known answer, written before any run.

| Field | Type | Plain-English description |
|---|---|---|
| `category` | string | Which scam category the script exercises, or `ordinary`. |
| `type` | string | `scam` or `genuine`. |
| `script_text` | string | The Hinglish script that was spoken. Kept so the test can be audited. |
| `timbre_voice` | string | `Nalini` or `Deepak`. |
| `audio_path` | string | The WAV file (an uncompressed sound format) in `samples\`. |
| `expected_label` | string | `scam` or `genuine`. |
| `created_at` | string (ISO 8601) | When the audio was generated. |

No `id` field — scenarios are identified by their position in the array and by `audio_path`. The ground truth (the known correct answer) is written when the scenario is created and is not editable from the results screen. A test whose answer can be changed after seeing the score is not a test.

### 2.5 Pattern

A scam-phrase rule. Lives in `data\patterns.json`, editable without touching code.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | e.g. `urgency_abhi_karna_hoga`. |
| `category` | string | One of the six categories. |
| `phrase_variants` | list of strings | Hinglish variants that should fire this rule, mixing Latin and Devanagari, e.g. `["abhi karna hoga", "abhi karna hai", "अभी करना होगा"]`. |
| `severity` | string | `high` (weight 0.4) or `medium` (weight 0.2). No `low` severity in the current set. |
| `weight` | number | Contribution to the Layer 2 risk: 0.2 for medium, 0.4 for high. |

---

## 3. Relationships

Small and flat on purpose. Nothing here needs a join (a database lookup that combines two tables) to be understood.

```
voiceprints (1) <-------- (many) incidents.layer1.comparisons[]   each comparison points at a voiceprint id
voiceprints (1) <-------- (0..1) incidents.claim.voiceprint_id
patterns    (1) <-------- (many) incidents.layer2.hits[]         each hit copies category and weight
patterns    (1) <-------- (many) selftest_runs.scenarios[].hits[]
scenarios   (1) <-------- (many) selftest_runs.scenarios[]       by scenario_id / audio_path
scenarios   (many) ------> (1) pattern category                   which rule family it is meant to exercise
```

Two deliberate choices:

- **Copied values, not pointers.** An incident stores the voiceprint name, the threshold, and the pattern weight at the time of the check. If a voiceprint is deleted or a weight is edited later, the old incident still reads correctly.
- **No cascade deletes.** Deleting a voiceprint never deletes history. The log keeps the name it saw.

---

## 4. Example JSON

### 4.1 One incident (compact)

```json
{
  "id": "inc_14bb8753a157",
  "checked_at": "2026-11-05T09:37:37+05:30",
  "created_at": "2026-11-05T09:37:37+05:30",
  "audio_path": "samples/gc_genuine_friend_dinner_20261105_093045.wav",
  "transcript": "हाय यार, मैं रोहन बोल रहा हूँ, आज शाम डिनर का प्लान बनाया है कैफे कॉफी डे में आठ बजे। टू फ्री हो तो आ जाना। मैं टेबल बुक कर दूंगा। अगर कोई प्रॉब्लम हो तो मैसेज कर देना। सी यू, टेक केयर।",
  "claim": {
    "detected_phrase": null,
    "role": null,
    "voiceprint_id": "vp_papa",
    "enrolled": true,
    "note": "no claim detected — comparing against the default voiceprint"
  },
  "layer1": {
    "comparisons": [
      {"voiceprint_id": "vp_papa", "name": "Nalini", "role": "Papa", "cosine": 0.8263,
       "threshold": 0.55, "verdict": "match", "target": true}
    ],
    "target_id": "vp_papa",
    "best_cosine": 0.8263,
    "threshold": 0.55,
    "label": "identity match",
    "comparable": true
  },
  "layer2": {
    "hits": []
  },
  "composite": 0,
  "band": "low",
  "verdict_sentence": "The caller's voice is consistent with the enrolled person and no scam patterns matched. This is a weak signal, not a clearance.",
  "notes": [
    "no claim detected — comparing against the default voiceprint",
    "Layer 1 compared against the default voiceprint (Papa)"
  ]
}
```

### 4.2 One self-test summary (compact)

```json
{
  "run_id": "run_20261107_182914_fa8e",
  "started_at": "2026-11-07T18:29:14+05:30",
  "threshold": 0.55,
  "scenario_count": 10,
  "metrics": {
    "scam_caught": "7/7",
    "genuine_passed": "3/3",
    "caution_count": 0,
    "errors": 0,
    "weakest": "family_emergency (composite 75, distance 0)",
    "weakest_category": "family_emergency",
    "weakest_composite": 75,
    "weakest_distance": 0
  },
  "scenarios": [
    {"scenario_id": "sc01_family_emergency", "category": "family_emergency",
     "expected_label": "scam", "hard_case": null,
     "audio_path": "samples/gc_scam_family_emergency_20261105_093045.wav",
     "composite": 75, "band": "high", "status": "caught", "distance": 0,
     "best_cosine": 0.2752,
     "hits": [
       {"id": "urgency_turant", "category": "urgency", "matched_phrase": "तुरंत",
        "transcript_snippet": "...", "severity": "medium", "weight": 0.2},
       {"id": "emotional_kisi_ko_mat_batao", "category": "emotional", "matched_phrase": "किसी को अभी मत बताना",
        "transcript_snippet": "...", "severity": "medium", "weight": 0.2}
     ],
     "error": null},
    {"scenario_id": "sc02_bank_fraud", "category": "bank_fraud",
     "expected_label": "scam", "hard_case": null,
     "audio_path": "samples/gc_scam_bank_fraud_20261105_093045.wav",
     "composite": 74, "band": "high", "status": "caught", "distance": 0,
     "best_cosine": 0.2894,
     "hits": [
       {"id": "urgency_turant", "category": "urgency", "matched_phrase": "तुरंत",
        "transcript_snippet": "...", "severity": "medium", "weight": 0.2},
       {"id": "otp_bank_otp_bata_do", "category": "otp_bank", "matched_phrase": "ओटीपी",
        "transcript_snippet": "...", "severity": "high", "weight": 0.4}
     ],
     "error": null}
  ]
}
```

---

## 5. Scoring inputs

Every number in the composite score traces to a stored field. The formula is written in `04_ARCHITECTURE.md`, Section 7. This table says where each input comes from.

| Score input | Stored field | How it is used |
|---|---|---|
| Highest cosine | highest `layer1.comparisons[].cosine` where `target` is true | Distance below the threshold becomes Layer 1 risk |
| Threshold | `layer1.threshold` | The cut-off in force for this check, kept so old results stay reproducible |
| Layer 1 pass or fail | `layer1.comparisons[].verdict` (`match`/`mismatch`) | Shown as evidence; feeds the risk number through the cosine margin |
| Hit count | length of `layer2.hits` | Used for display, not multiplied into the score |
| Hit weights | `layer2.hits[].weight` | Summed, divided by 0.8, capped at 1.0, becomes Layer 2 risk |
| Hit severity | `layer2.hits[].severity` | Drives the colour and ordering in the UI and PDF |
| Composite | `composite` | `round(100 * (0.5 * layer1_risk + 0.5 * layer2_risk))` |
| Band | `band` | 0–29 `low`, 30–59 `caution`, 60–100 `high` |

**Missing comparison case.** When `claim.detected_phrase` is null, Layer 1 has no target row and `layer1.label` is `not comparable` with `comparable: false`. The composite then uses Layer 2 risk alone, rescaled to 0–100, and the record keeps that fact so the PDF can say why.

**Reproducibility rule.** Because the threshold and the weights are copied into the incident, an old check can be recomputed exactly, even after the config changes. A score that cannot be recomputed from its own record is a bug.

---

## 6. Retention and privacy

- **Files stay local.** `data\`, `samples\`, and `reports\out\` live on this machine. No sync, no cloud backup, no analytics.
- **Audio is kept for review** until the user deletes it. Generated scenario audio is safe to keep; an uploaded real recording should be deleted when it is no longer needed.
- **Nothing is uploaded beyond the Gnani calls needed for analysis.** That means the audio sent for transcription and embedding, and the verdict text sent for speech. The incident log, the PDFs, and the voiceprints are never uploaded.
- **No account data.** There is no login, no email, no user profile. The personal data is limited to what the user types when enrolling a voice: a display name and a role.
- **The API key is not stored in any record.** It stays in the environment variable `GNANI_API_KEY` and is read at call time.
- **Deleting a voiceprint does not delete history.** Incidents keep the name and score they recorded, which is what makes the log trustworthy.
- **Caches make re-runs free.** `stt_cache.json` and `embedding_cache.json` are keyed by absolute path + file size + mtime; running the pipeline again on the same files costs 0 API credits.
- **Demo rule.** Use generated audio. No real victim recording and no real scam call without consent.

---

*Last updated: 8 November 2026. This is a living document: after the build, open each file in `data\`, compare it with these tables, and fix every field name that drifted.*
