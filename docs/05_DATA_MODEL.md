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
| Self-test runs | `data\selftest_runs.json` | One record per battery run |
| Scenarios | `data\scenarios.json` | One record per generated test call |
| Patterns | `data\patterns.json` | One record per scam-phrase rule |

**Why JSON here.**

- One user, one machine, small numbers of records. A database server adds a process to start and a dependency to install, and buys nothing at this size.
- Human-readable. A judge, or future-me, can open the file and see what was stored without a tool.
- Easy to back up: copy the folder.
- Easy to compare line by line in git, which supports the dated ownership trail.
- No schema migration step when a field is added mid-build.

**Alternative: SQLite** (a small single-file database). Use it if the incident log grows past a few thousand rows, or if the UI needs filtered queries and joins across collections (a join is a lookup that combines records from two collections). The record shapes in Section 2 are written so they map to tables without redesign: each list becomes a child table with a parent id.

**Marked: default, changeable during build.** Switching engines is a code change in one storage module, not a rewrite of the pipeline, as long as nothing outside that module opens the files directly.

**Write rules.**

- Records are added, never edited. For incidents and self-test runs, a record does not change after the check completes, except to attach `pdf_path`.
- Write the incident before generating a PDF, so a report failure cannot lose the check.
- Write to a temp file, then rename, so a crash mid-write cannot leave half a JSON file.
- One list per file, no nested top-level objects.

---

## 2. Entities

Five record types. Every field below appears in the files exactly as named.

### 2.1 Enrolled voiceprint

A stored fingerprint of a trusted person's voice.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | Short identifying label, e.g. `vp_0001`. Used everywhere else to refer to this person. |
| `display_name` | string | The name shown in the app, e.g. "Ramesh". |
| `role_or_relationship` | string | The role a caller might claim, e.g. "Papa", "CEO". The claimed-identity resolver matches against this. |
| `created_at` | string (ISO 8601) | When the voiceprint was enrolled, in a standard date-and-time text format, e.g. `2026-11-04T10:12:00+05:30`. |
| `embedding` | list of 768 numbers | The voice fingerprint itself. Stored as decimal numbers, not as base64 (a way of packing binary data as text characters), so it stays readable and comparable. |
| `source_audio_path` | string | Where the enrollment WAV lives, e.g. `samples\A1_nalini_X.wav`. |
| `notes` | string or null | Free text: which recording, which device, anything worth remembering. |

Rules: `role_or_relationship` is the lookup key for claims, so it must be short and consistent ("Papa", not "my father"). Re-enrolling the same `role_or_relationship` offers to replace the existing record rather than silently creating a duplicate.

### 2.2 Incident

One record per completed check. This is the record the incident log lists and the PDF report renders.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | Identifying check id, e.g. `inc_0007`. Printed on the PDF. |
| `checked_at` | string (ISO 8601) | When the check ran. |
| `caller_audio_path` | string | The audio file that was analysed. |
| `transcript` | string | The full text Prisma (Gnani's speech-to-text service) returned. |
| `claimed_identity` | object or null | The claim that was detected: `phrase`, `resolved_voiceprint_id`, `resolution` ("exact role label", "alias", "no match"). `null` when no claim was found. |
| `layer1` | list of comparison objects | One entry per voiceprint compared. See below. |
| `layer1_verdict` | string | `match`, `mismatch`, or `not_comparable`. |
| `layer2_hits` | list of hit objects | One entry per matched pattern. See below. |
| `layer2_verdict` | string | `hits_found` or `no_hits`. |
| `composite_score` | integer 0–100 | The combined risk number. |
| `overall_verdict` | string | `low`, `caution`, or `high`. |
| `spoken_verdict_text` | string | The exact sentence sent to Timbre (Gnani's text-to-speech service), so the audio and the screen can be compared later. |
| `pdf_path` | string or null | Where the report was saved (PDF, a document format that opens the same way on any machine). `null` until the user exports. |
| `notes` | string or null | Anything the user typed about this call. |

**Layer 1 comparison object.**

| Field | Type | Description |
|---|---|---|
| `voiceprint_id` | string | Which enrolled person was compared. |
| `display_name` | string | Copied in for readability, so the log survives a deleted voiceprint. |
| `cosine` | number | The similarity score, 0 to 1, where 1 means identical voices, rounded to four decimals. |
| `threshold` | number | The cut-off in force at the time of the check. |
| `passed` | boolean (a true/false value) | `true` when `cosine >= threshold`. |
| `is_target` | boolean | `true` for the voiceprint the claim pointed at, or the default when no claim was found. |

**Layer 2 hit object.**

| Field | Type | Description |
|---|---|---|
| `category` | string | One of the six categories in `04_ARCHITECTURE.md`, Section 6. |
| `matched_phrase` | string | The exact variant that fired. |
| `transcript_snippet` | string | About 80 characters either side of the match. |
| `severity` | string | `low`, `medium`, or `high`. |
| `weight` | number | The pattern's contribution to the score. |

### 2.3 Self-test run

One record per battery run.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | e.g. `str_0003`. |
| `run_at` | string (ISO 8601) | When the battery started. |
| `scenarios` | list of result objects | One entry per scenario attempted. See below. |
| `summary` | object | `scam_caught`, `scam_total`, `genuine_passed`, `genuine_total`, `caution_count`, `error_count`, `weakest_scenario`, `threshold_used`, `threshold_sweep`. |
| `scorecard_pdf_path` | string or null | Where the scorecard PDF was saved. |

**Scenario result object.**

| Field | Type | Description |
|---|---|---|
| `scenario_id` | string | Points at a record in `scenarios.json`. |
| `type` | string | `scam` or `genuine`. |
| `category` | string | The scam category, or `ordinary` for genuine calls. |
| `expected_label` | string | `high` for scam, `low` for genuine. |
| `actual_verdict` | string | `low`, `caution`, `high`, or `error`. |
| `score` | integer or null | The composite score, `null` when the run errored. |
| `caught` | boolean or null | `true` when a scam scored `high`, or a genuine call scored `low`. `null` on error. |

Errors are recorded as `actual_verdict = "error"` with `caught = null`. They are never folded into the caught or passed counts.

### 2.4 Scenario (generated test call)

A single generated call with a known answer, written before any run.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | e.g. `scn_0012`. |
| `category` | string | Which scam category the script exercises, or `ordinary`. |
| `type` | string | `scam` or `genuine`. |
| `script_text` | string | The Hinglish script that was spoken. Kept so the test can be audited. |
| `timbre_voice` | string | `Nalini` or `Deepak`. |
| `audio_path` | string | The WAV file (an uncompressed sound format) in `samples\`. |
| `expected_label` | string | `high` for scam, `low` for genuine. |
| `created_at` | string (ISO 8601) | When the audio was generated. |

The ground truth (the known correct answer) is written when the scenario is created and is not editable from the results screen. A test whose answer can be changed after seeing the score is not a test.

### 2.5 Pattern

A scam-phrase rule. Lives in `data\patterns.json`, editable without touching code.

| Field | Type | Plain-English description |
|---|---|---|
| `id` | string | e.g. `pat_otp_01`. |
| `category` | string | One of the six categories. |
| `phrases` | list of strings | Hinglish variants that should fire this rule, e.g. `["otp bata do", "otp share karo", "code batao"]`. |
| `severity` | string | `low`, `medium`, or `high`. |
| `weight` | number | Contribution to the Layer 2 risk, 0.1 to 0.4. |

---

## 3. Relationships

Small and flat on purpose. Nothing here needs a join (a database lookup that combines two tables) to be understood.

```
voiceprints (1) <-------- (many) incidents.layer1[]      each comparison points at a voiceprint id
voiceprints (1) <-------- (0..1) incidents.claimed_identity.resolved_voiceprint_id
patterns    (1) <-------- (many) incidents.layer2_hits[]  each hit copies category and weight
scenarios   (1) <-------- (many) selftest_runs.scenarios[]
scenarios   (many) ------> (1) pattern category           which rule family it is meant to exercise
```

Two deliberate choices:

- **Copied values, not pointers.** An incident stores the voiceprint name, the threshold, and the pattern weight at the time of the check. If a voiceprint is deleted or a weight is edited later, the old incident still reads correctly.
- **No cascade deletes.** Deleting a voiceprint never deletes history. The log keeps the name it saw.

---

## 4. Example JSON

### 4.1 One incident (compact)

```json
{
  "id": "inc_0007",
  "checked_at": "2026-11-04T10:42:11+05:30",
  "caller_audio_path": "samples\\scn_0012_papa_scam.wav",
  "transcript": "Beta main papa bol raha hoon, accident ho gaya, abhi 50000 bhejo, kisi ko mat batao.",
  "claimed_identity": {
    "phrase": "main papa bol raha hoon",
    "resolved_voiceprint_id": "vp_0001",
    "resolution": "exact role label"
  },
  "layer1": [
    {"voiceprint_id": "vp_0001", "display_name": "Ramesh", "cosine": 0.3121,
     "threshold": 0.55, "passed": false, "is_target": true}
  ],
  "layer1_verdict": "mismatch",
  "layer2_hits": [
    {"category": "authority impersonation", "matched_phrase": "main papa bol raha hoon",
     "transcript_snippet": "Beta main papa bol raha hoon, accident ho gaya",
     "severity": "high", "weight": 0.4},
    {"category": "emotional manipulation", "matched_phrase": "kisi ko mat batao",
     "transcript_snippet": "abhi 50000 bhejo, kisi ko mat batao",
     "severity": "medium", "weight": 0.2},
    {"category": "deceptive call to action", "matched_phrase": "50000 bhejo",
     "transcript_snippet": "accident ho gaya, abhi 50000 bhejo",
     "severity": "high", "weight": 0.4}
  ],
  "layer2_verdict": "hits_found",
  "composite_score": 72,
  "overall_verdict": "high",
  "spoken_verdict_text": "Voice match is low. The call also used a family emergency claim and asked for secrecy. Overall risk is high.",
  "pdf_path": null,
  "notes": null
}
```

### 4.2 One self-test summary (compact)

```json
{
  "id": "str_0003",
  "run_at": "2026-11-04T11:05:00+05:30",
  "scenarios": [
    {"scenario_id": "scn_0012", "type": "scam", "category": "family emergency",
     "expected_label": "high", "actual_verdict": "high", "score": 72, "caught": true},
    {"scenario_id": "scn_0021", "type": "genuine", "category": "ordinary",
     "expected_label": "low", "actual_verdict": "low", "score": 12, "caught": true}
  ],
  "summary": {
    "scam_caught": 5, "scam_total": 6,
    "genuine_passed": 3, "genuine_total": 4,
    "caution_count": 1, "error_count": 1,
    "weakest_scenario": "scn_0019",
    "threshold_used": 0.55,
    "threshold_sweep": [{"threshold": 0.50, "scam_caught": 4, "genuine_passed": 4},
                        {"threshold": 0.55, "scam_caught": 5, "genuine_passed": 3},
                        {"threshold": 0.60, "scam_caught": 6, "genuine_passed": 2}]
  },
  "scorecard_pdf_path": "reports\\out\\scorecard_str_0003.pdf"
}
```

---

## 5. Scoring inputs

Every number in the composite score traces to a stored field. The formula is written in `04_ARCHITECTURE.md`, Section 7. This table says where each input comes from.

| Score input | Stored field | How it is used |
|---|---|---|
| Highest cosine | highest `layer1[].cosine` where `is_target` is true | Distance below the threshold becomes Layer 1 risk |
| Threshold | `layer1[].threshold` | The cut-off in force for this check, kept so old results stay reproducible |
| Layer 1 pass or fail | `layer1[].passed` | Shown as evidence; feeds the risk number through the cosine margin |
| Hit count | length of `layer2_hits` | Used for display, not multiplied into the score |
| Hit weights | `layer2_hits[].weight` | Summed, divided by 0.8, capped at 1.0, becomes Layer 2 risk |
| Hit severity | `layer2_hits[].severity` | Drives the colour and ordering in the UI and PDF |
| Composite | `composite_score` | `round(100 * (0.5 * layer1_risk + 0.5 * layer2_risk))` |
| Band | `overall_verdict` | 0–29 `low`, 30–59 `caution`, 60–100 `high` |

**Missing comparison case.** When `claimed_identity.resolution` is "no match", Layer 1 has no target row and `layer1_verdict` is `not_comparable`. The composite then uses Layer 2 risk alone, rescaled to 0–100, and the record keeps that fact so the PDF can say why.

**Reproducibility rule.** Because the threshold and the weights are copied into the incident, an old check can be recomputed exactly, even after the config changes. A score that cannot be recomputed from its own record is a bug.

---

## 6. Retention and privacy

- **Files stay local.** `data\`, `samples\`, and `reports\out\` live on this machine. No sync, no cloud backup, no analytics.
- **Audio is kept for review** until the user deletes it. Generated scenario audio is safe to keep; an uploaded real recording should be deleted when it is no longer needed.
- **Nothing is uploaded beyond the Gnani calls needed for analysis.** That means the audio sent for transcription and embedding, and the verdict text sent for speech. The incident log, the PDFs, and the voiceprints are never uploaded.
- **No account data.** There is no login, no email, no user profile. The personal data is limited to what the user types when enrolling a voice: a display name and a role.
- **The API key is not stored in any record.** It stays in the environment variable `GNANI_API_KEY` and is read at call time.
- **Deleting a voiceprint does not delete history.** Incidents keep the name and score they recorded, which is what makes the log trustworthy.
- **Demo rule.** Use generated audio. No real victim recording and no real scam call without consent.

---

*Last updated: 4 November 2026. This is a living document: after the build, open each file in `data\`, compare it with these tables, and fix every field name that drifted.*
