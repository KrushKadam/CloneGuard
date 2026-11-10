# CloneGuard — Threat Model

## Assets

| Asset | Description | Sensitivity |
|---|---|---|
| `GNANI_API_KEY` | Cloud API credential for STT, TTS, voiceprint | High — bills credits, allows API calls |
| Voiceprint embeddings (`data/voiceprints.json`) | 768-dim biometric vectors of enrolled persons | High — biometric data, personal identifiers |
| Call transcripts / incident log (`data/incidents.json`) | Transcripts, claimed identity, scores, verdicts | High — PII, conversation content |
| Sample audio (`samples/`) | Reference recordings (genuine + scam) | Medium — voice samples, scripted content |
| Generated PDF reports (`reports/out/`) | Evidence PDFs with scores, phrases, transcripts | Medium — derived from above |

## Actors

| Actor | Trust Level | Access |
|---|---|---|
| Device owner (you) | Trusted | Full — runs app, sets env var, views data |
| Other local users | Untrusted (same OS) | Can read files if OS permissions allow |
| Public GitHub readers | Untrusted | See repo contents only (no runtime access) |
| Network neighbors (same LAN) | Untrusted | No direct access (localhost only) |

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│ Browser (localhost:8501)                                        │
│   └─ Streamlit UI — renders pages, accepts uploads              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP (local loopback)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Streamlit Python Process                                        │
│   ├─ app.py — orchestration, file upload, session state         │
│   ├─ engine/pipeline.py — run_check, save_record                │
│   ├─ engine/layer1.py — voiceprint enroll/compare               │
│   ├─ engine/layer2.py — transcript pattern scan                 │
│   ├─ voiceprint.py — Gnani embeddings API (HTTPS)               │
│   ├─ gnani.py — Prisma STT, Timbre TTS (HTTPS)                  │
│   └─ config.py — paths, thresholds, weights                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS (api.vachana.ai)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Gnani Cloud APIs                                                │
│   ├─ POST /api/v1/tts/voice-clone/embeddings (voiceprint)       │
│   ├─ POST /stt/v3 (transcription)                               │
│   └─ POST /api/v1/tts/inference (TTS)                           │
└─────────────────────────────────────────────────────────────────┘

Disk Storage (local):
  data/voiceprints.json, incidents.json, embedding_cache.json,
  stt_cache.json, selftest_runs.json, patterns.json, scenarios.json
  reports/out/*.pdf
```

## STRIDE Analysis

| Threat | Realistic Risk for This App | Current Control |
|---|---|---|
| **Spoofing** | Attacker claims to be enrolled person | Layer 1 cosine threshold (0.55) + claim-phrase resolution to specific voiceprint |
| **Tampering** | Modify uploaded audio, incident log, or voiceprints | WAV header check in `save_upload()`; JSON files append-only via `pipeline.save_record()`; no auth on local files |
| **Repudiation** | Owner denies a check was run | Incident log writes timestamped entry per check (`pipeline.save_record`) |
| **Information Disclosure** | Voiceprints, transcripts, API key leak to GitHub | `.gitignore` excludes `data/`, `reports/out/`, `.env`; key never printed (boolean check only in `api_key_present()`) |
| **Denial of Service** | Large uploads fill disk / crash app | `max_upload_size=25` on both uploaders + hard guard in `save_upload()` raising `ValueError` > 25 MB |
| **Elevation of Privilege** | Local user escalates via app | App runs as current user; no sudo, no setuid, no network listeners beyond localhost |

---
*Threat model written 9 November 2026. Matches code at commits `1cdeb5a`, `8d0deb6`.*