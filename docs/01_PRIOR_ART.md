# CloneGuard — Prior Art & Competitive Analysis

**Prepared:** 4 November 2026  
**Author:** CloneGuard project (team of two)  
**Purpose:** answer the question "hasn't this been done?" with sources instead of assertion.  
**Companion document:** `docs/02_POSITIONING.md`

---

## 1. Purpose and method

### 1.1 Why this document exists

CloneGuard is a voice-fraud check built on Gnani voice APIs (cloud web services that do the voice and text work). Before describing what it adds, this document maps what already exists: enterprise products, open-source and hackathon projects, consumer apps, and peer-reviewed research.

The document is written to be useful to a skeptical reader. It names the competitors, links the sources, marks what was actually fetched, and states where the evidence stops. It does not claim that any feature is absent from the market. A partial search cannot establish absence.

### 1.2 The two sweeps

| Sweep | Who ran it | What it covered | Output |
|---|---|---|---|
| Primary sweep | Assistant web research, 4 Nov 2026 | Vendor sites, GitHub search and API, ACL Anthology, Nature, arXiv, Crossref, DOI resolution | Source-by-source verification log (Section 7) |
| Second sweep | Independent ChatGPT research pass, 4 Nov 2026 | Additional vendor and repository names, consumer tools, research leads | Leads; not treated as verified until cross-checked |

The two sweeps were run independently and then compared. Where the second sweep named something the primary sweep could not fetch, it is labelled as reported rather than verified.

### 1.3 Verification standard

Every source in this document carries one of two labels:

- **[VERIFIED — fetched directly by primary sweep]** — the URL was fetched on 4 Nov 2026 and the described text was read at the source. For GitHub repositories, the repository page or GitHub API response was read.
- **[SECOND-SWEEP REPORTED — not independently fetched]** — the source was named by the independent sweep but could not be fetched or confirmed during the primary sweep.

"Verified" means the source says what is attributed to it. It does **not** mean the source's performance claims are true. Vendor accuracy figures, patent counts, and incident totals in this document are reported claims, not independent test results.

### 1.4 Limitations of the sweep

- The native web-search tool returned HTTP 402/429 (quota and rate limits) during part of the sweep.
- Workarounds used: direct URL fetches, DuckDuckGo HTML results, GitHub search, and the GitHub REST API.
- Some vendor pages are JavaScript-heavy or bot-blocked. IEEE Xplore returned HTTP 202 with an empty body for one paper; its metadata was confirmed through Crossref instead.
- One company site (Reality Defender) did not resolve via DNS during the sweep.
- Repository counts are a snapshot of one day. GitHub search results change.
- The sweep is partial. It cannot prove that a similar tool does not exist, and no such claim is made anywhere in this document.

---

## 2. Enterprise products

| Product | What it does | Source | Status |
|---|---|---|---|
| **Pindrop** — Pulse for Contact Centers, Passport, VeriCall, Protect | Identity trust platform for voice and video. Pulse identifies synthetic speech in phone interactions; Passport enrolls and authenticates known callers; VeriCall adds ANI validation (ANI is the phone number a call arrives from) and spoof detection; Protect scores fraud risk during a live interaction. | <https://www.pindrop.com/> | [VERIFIED — fetched directly by primary sweep] |
| **Resemble AI** — Detect, Identity, Intelligence | Multimodal deepfake detection (spotting AI-generated fakes) for audio, video, and images. Detect covers voice clones and carrier call infrastructure, 54 languages, and 250+ generative models tested. Identity enrolls and authenticates a voice. Intelligence provides an explainability layer. The site has a dedicated executive-impersonation use case. | <https://www.resemble.ai/> and <https://www.resemble.ai/products/detect/> | [VERIFIED — fetched directly by primary sweep] |
| **Reality Defender** | Deepfake detection platform. Its existence and general positioning are corroborated by Resemble's public comparison page. The company site itself was unreachable during the sweep (DNS failure). | <https://www.resemble.ai/resemble-ai-vs-reality-defender> | [SECOND-SWEEP REPORTED — not independently fetched] |

### 2.1 Pindrop

Pindrop's homepage describes an "identity trust layer for real-time communications" and lists four relevant products: Pulse (synthetic speech), Passport (known-caller authentication), VeriCall (ANI validation and spoof detection), and Protect (live fraud-risk scoring). The same page reports 300+ patents, 15+ years of operation, and 8B+ interactions analyzed. It also reports a 1680% spike in AI attacks, attributed to Pindrop's own analysis of fraud data from autumn 2024 to spring 2026.

Those are vendor figures. They are useful as evidence that the problem is commercially serious. They are not independent measurements.

### 2.2 Resemble AI

Resemble sells detection as an API and as integrations into carrier and meeting infrastructure. Its Detect page reports 54 languages validated against MLAADv10, 250+ generative models tested, and audio detection accuracy of 99.5% on the Podonos benchmark cited on its site. Its Identity product enrolls a voice and matches a later sample against it — the same broad idea as CloneGuard's Layer 1, delivered as an enterprise service.

Resemble's H1 2026 Deepfake Threat Report reports **821 verified deepfake attacks in six months, drawn from 1,760 news reports**. This is an all-media count (audio, video, image), not a count of voice incidents alone. It should be quoted with that qualifier.

### 2.3 Reality Defender

Reality Defender appears repeatedly in Resemble's public comparison material as a deepfake-detection competitor. The primary sweep could not open Reality Defender's own site, so this document does not describe its product line beyond that corroborated existence.

### 2.4 What this establishes

Voiceprint enrollment plus synthetic-speech detection is already a product category, sold to banks, insurers, contact centers, and meeting platforms. The enterprise layer is real, funded, and patent-heavy. CloneGuard does not enter an empty market.

---

## 3. Open-source and hackathon projects

| Project | What it is | Source | Status |
|---|---|---|---|
| **VoxDetect** (`io-PEAK/VoxDetect`) | Full-stack voice-clone detection prototype. README claims real-time call analysis that fuses a Wav2Vec2 deepfake classifier (Wav2Vec2 is a speech model that learns from raw audio) with prosody (voice rhythm and pitch patterns), voiceprint, and call-context signals into a 0–100 risk score. 0 stars, 4 forks, 97 commits, GPL-3.0. | <https://github.com/io-PEAK/VoxDetect> | [VERIFIED — fetched directly by primary sweep; README claims not independently evaluated] |
| **SIH26104** | Official AICTE Smart India Hackathon 2026 problem statement: "AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks." Organization: AICTE Cyber Security Cell. Theme: Blockchain & Cybersecurity. Idea-submission deadline: 30 September 2026. | <https://github.com/vedantchalke36/sih-2026-problem-statements/blob/main/ps_2026/SIH26104.md> and <https://www.sihbuddy.in/ps/SIH26104> | [VERIFIED — fetched directly by primary sweep; mirror cites sih.gov.in/sih2026PS as its source] |
| **GitHub search: "voice clone SIH 2026"** | 28 repositories returned on 4 Nov 2026; the eight checked individually had 0–1 stars. Examples below. | GitHub REST search API | [VERIFIED — fetched directly by primary sweep] |
| **GitHub search: "voice clone detection fraud"** | 55 repositories returned on 4 Nov 2026, including earlier SIH cohorts and general prototypes. | GitHub REST search API | [VERIFIED — fetched directly by primary sweep] |
| **VIGIL, AI Voice Guard, VoiceShield, VoxGuard, VaaneeShield, VoxSatya** | Described by the second sweep as SIH-related repositories with voiceprint and risk-scoring architectures. VoxSatya's README reportedly says production code is kept private. | Named by second sweep; no single canonical URL confirmed | [SECOND-SWEEP REPORTED — not independently fetched] |

### 3.1 VoxDetect

VoxDetect is the closest architectural match found in open source. Its README describes a four-signal fusion: a Wav2Vec2 deepfake classifier, prosody anomaly, ECAPA-TDNN voiceprint cosine similarity (a 0-to-1 score where 1 means identical voices), and call-context flags. It reports a React dashboard, FastAPI backend, SQLite evidence log, and a live-microphone demo.

At the time of the sweep it had 0 stars and 4 forks. That is an observation about reach, not a judgment about code quality. The README is a design document with claims; the sweep did not run the project or audit its evaluation.

### 3.2 SIH26104

SIH26104 is the national problem statement that many of the student repositories are built around. It asks for real-time detection of cloned or synthetic speech, a risk score, multilingual support for Indian accents and dialects, privacy-preserving design, and APIs for banks and telecoms.

The existence of SIH26104 matters for two reasons:

1. The problem is validated at national scale by AICTE.
2. Judges and reviewers have likely seen many submissions on the same theme. The differentiator cannot be the problem statement itself.

### 3.3 GitHub repository counts and examples

The search "voice clone SIH 2026" returned 28 repositories. These eight were checked individually through the GitHub API:

| Repository | Stars | Short description |
|---|---:|---|
| `TAHIRIZZM/VoiceGuard-SIH2026` | 0 | AI-powered real-time voice clone detection and prevention, SIH 2026 |
| `voiceshield-team/voiceshield-sih-2026` | 0 | Streaming audio analysis and prevention platform for SIH 2026 |
| `Kevinmatthew1011/sih26104-voice-cloning-detection` | 1 | Detection platform for SIH26104 |
| `Muhamed-Arif/SIH26104-Voice-Clone-Detection` | 0 | Detection and prevention for SIH 2026 |
| `kushwahayashh/sih26104-voice-guard` | 0 | Detection and prevention for SIH26104 |
| `contactyuvrajsonkar-eng/ClearVoiceShield-SIH2026` | 0 | Real-time voice cloning and impersonation detection |
| `malvikasubhash/verivoice-sih-2026` | 0 | "X-SPECT" voice cloning detection prototype |
| `neemaabhishek1677-hue/AI_Voicecloning_for_SIH2026` | 1 | Privacy-preserving detection framework |

The earlier search "voice clone detection fraud" returned 55 repositories. Examples include `divyansh-git-max/VoiceGuard` (5 stars, real-time phone-call detection), `robinxheart/VoiceShield-Ai` (1 star, SIH25104), `Maanii-21/VISHWAS-SETU` (0 stars), `maanyajain09/Swar-Netra` (0 stars, Android), and `jeevikavijay07-ai/VoiceGuard-AI` (0 stars).

One repository named by the earlier sweep, `guptaaditi07/truevox`, returned HTTP 404 on recheck. It may have been renamed or removed, so it is not counted in the table.

### 3.4 What this establishes

The idea is well represented among student teams, and at least one open-source project (VoxDetect) already combines deepfake classification, voiceprint matching, prosody, and context scoring. CloneGuard cannot present that combination as a new idea.

The student repositories appear early-stage: small star counts, recent activity dates, and README-scale documentation. This is an opportunity for execution and evidence, not for an idea claim.

---

## 4. Consumer products

| Product | What it does | Source | Status |
|---|---|---|---|
| **Tring** | Indian AI call assistant. Answers missed calls in 12+ Indian languages including Hindi and Hinglish, blocks spam, provides live transcripts, and can answer in a clone of the user's own voice. It does not document enrolled-person voiceprint verification or clone detection. | <https://heytring.com/> | [VERIFIED — fetched directly by primary sweep] |
| **VigilAI** | Accessible audio and video deepfake detector. Its documentation describes language-independent audio analysis. A full voiceprint-plus-scam-pipeline is not documented. | Named by second sweep; site not fetched | [SECOND-SWEEP REPORTED — not independently fetched] |

### 4.1 Tring

Tring is the most relevant consumer product found in India. It handles the call, speaks Indian languages, blocks spam, and even clones the user's own voice for answering. That last feature is adjacent to CloneGuard's technology but has the opposite purpose: it creates a consented synthetic voice rather than checking whether an incoming voice matches an enrolled person.

Tring's public page does not describe a trusted-person voiceprint check or a scam-pattern transcript scan. That is a statement about its public documentation, not about its private roadmap.

### 4.2 What this establishes

Consumer voice AI in India is active, but the reviewed products cluster around call handling, spam blocking, and media verification. A free, local-interface tool that checks a caller against an enrolled person and scans the transcript for Hinglish fraud patterns is not represented in this sweep.

Absence from a partial sweep is not proof of a market gap. It is a reason to describe CloneGuard's contribution at the feature level and let the demo carry the argument.

---

## 5. Research literature

| Work | Contribution | Relevance to CloneGuard | Source | Status |
|---|---|---|---|---|
| **ASVspoof challenge series, 2015–2024** | International benchmark for spoofing and anti-spoofing against speaker verification, including deepfake and TTS/voice-conversion tracks. | Establishes that synthetic-speech detection is a decade-old research field with standard metrics (EER, the equal error rate, and t-DCF, the tandem detection cost function). | <https://www.asvspoof.org/> | [VERIFIED — fetched directly by primary sweep] |
| **Liu et al., "ASVspoof 2021: Towards Spoofed and Deepfake Speech Detection in the Wild"** | Summary paper for the 2021 challenge; IEEE/ACM TASLP. | Shows the field has moved toward in-the-wild and compressed-audio conditions. | <https://arxiv.org/abs/2210.02437>; DOI 10.1109/TASLP.2023.3285283 | [VERIFIED — fetched directly by primary sweep] |
| **Hmimou, Tabaa, Khiat & Hidila (2026), "A Multilingual Behavioral Speech Dataset for Vishing and Social Engineering Detection"** | VISHGUARD: 3,000 simulated phone calls in English, French, and Modern Standard Arabic, balanced between fraudulent and legitimate, annotated for persuasion strategy and emotional tone. | Closest research analogue to CloneGuard's Layer 2: scam-language analysis over telephony-style audio. | *Scientific Data* 13, Article 1456 (2026); DOI 10.1038/s41597-026-07724-z | [VERIFIED — fetched directly by primary sweep] |
| **Sharma, Ekbote & Gupta (2025), "IndicSynth"** | 4,000 hours of synthetic speech from 989 target speakers across 12 Indian languages. ACL 2025 Outstanding Paper. | Indian-language synthetic-speech data and a baseline for why detectors trained on English alone generalize poorly. | <https://aclanthology.org/2025.acl-long.1070/> | [VERIFIED — fetched directly by primary sweep] |
| **Gaikawad & Ghosh (2025), "A Robust and Lightweight CNN-Transformer Model for Audio Deepfake Detection in Indian Languages"** | Lightweight CNN-Transformer evaluated on Marathi, Hindi, Tamil, Telugu, Malayalam, and Kannada. | Evidence that Indian-language audio deepfake detection is an active research target, not a blank space. | IEEE Xplore doc 11039572; DOI 10.1109/ISPCC66872.2025.11039572 | [VERIFIED — fetched directly by primary sweep; metadata confirmed via Crossref] |
| **Meena, Dayanvita, Singh et al., "Transliterated Hindi text phishing detection using machine learning"** | Machine-learning detection of phishing in transliterated Hindi (Hinglish) text. | Direct precedent for treating Hinglish text patterns as a fraud signal. | Taylor & Francis chapter; DOI 10.1201/9781003731689-104 | [VERIFIED — fetched directly by primary sweep] |
| **"Voice Cloning: Comprehensive Survey"** | Survey of voice-cloning methods, risks, and detection. | Confirms the breadth of the field. | <https://arxiv.org/abs/2505.00579> | [VERIFIED — fetched directly by primary sweep] |
| **"A survey of AI-generated voices and their detection"** | Survey of generated-voice detection. | Confirms an established detection literature. | Emerald; DOI 10.1108/ATSIP-09-2025-0093 | [VERIFIED — fetched directly by primary sweep] |

### 5.1 What the research says, in plain terms

- Detecting synthetic speech from acoustic artifacts is a mature benchmark problem. ASVspoof has run since 2015.
- Indian-language synthetic speech is an active subfield, with IndicSynth and several Indian-language detector papers.
- Scam-language analysis is also studied, including multilingual vishing (voice-phishing) corpora and Hinglish phishing text.
- VISHGUARD is a synthetic corpus: its calls were generated with TTS and mixed with ambient noise, not recorded from real phone lines. The authors describe the noise as approximating office, street, and home environments rather than full telecom-channel effects. That is a useful honesty benchmark for CloneGuard's own generator.

### 5.2 What this establishes

The research ingredients behind CloneGuard — speaker embeddings, cosine verification, synthetic-speech detection, and scam-text classification — are all published and benchmarked. CloneGuard is an integration and product effort, not a research contribution.

---

## 6. What this means for CloneGuard

### 6.1 The space is crowded

- **Enterprise:** Pindrop and Resemble sell identity verification and deepfake detection to large organizations, with patents, integrations, and years of operating data.
- **Hackathon:** SIH26104 made voice-clone impersonation a national problem statement, and a GitHub search for "voice clone SIH 2026" returned 28 repositories, many of them student projects on this theme.
- **Research:** ASVspoof, IndicSynth, VISHGUARD, and multiple Indian-language detector papers cover the underlying science.

### 6.2 No novelty claim

CloneGuard does **not** claim that voiceprint verification plus fraud analysis is a new combination. VoxDetect's README describes a similar fusion. Pindrop and Resemble productize adjacent capabilities. SIH teams are building against the same brief.

The honest claim is narrower: a complete, measurable, explainable implementation on Gnani APIs, with a self-test loop and evidence output that the reviewed consumer tools do not advertise.

### 6.3 Feature-level distinctions

These are descriptions, not superlatives. Each one can be demonstrated.

| Distinction | Why it matters | Honest caveat |
|---|---|---|
| **Free local desktop interface** | A reviewer can run it without a sales call or enterprise contract. | The interface is local; inference runs on Gnani's cloud APIs, so internet access and API credentials are required. |
| **All three Gnani APIs in one flow** | Voiceprint (Voice-Clone embeddings), transcription (Prisma), and speech (Timbre) are composed into one verdict, including a spoken result. | This is integration engineering, not a new model. |
| **Built-in Hinglish scam-call generator** | The demo is self-contained: it can produce scam and genuine calls with Timbre voices and phone-line noise. | The calls are synthetic. They test the pipeline against known scripts, not against real fraudsters. |
| **Self-Test Harness** | The tool generates a battery of scam and genuine calls, runs them through the full pipeline, prints a calibration scorecard, and exports a PDF. It attacks itself and publishes the result. | It measures calibration against its own generator. A good score is not a claim of real-world accuracy. |
| **Claimed-identity multi-voiceprint flow** | If the caller says "Main Papa bol raha hoon" or names a CEO, the app checks that person's enrolled voiceprint rather than a generic one. | It depends on correct name extraction from the transcript; a missed or ambiguous claim falls back to the default enrolled voice. |
| **PDF evidence report and incident log** | Each check produces a shareable record with both layer scores and transcript evidence. | It is an evidence aid, not a case-management or chain-of-custody system. |

A note on the self-test distinction: none of the consumer tools reviewed in this sweep advertises an adversarial self-test harness. That is a statement about the reviewed public pages, not a claim that no such tool exists anywhere.

### 6.4 Known limitations

These must be stated wherever CloneGuard is described.

1. **A good clone of the enrolled voice can pass Layer 1.** If the cloned audio is clean and the words are ordinary, the voiceprint may fall inside the acceptance range. Layer 2 and human judgment are the remaining signals.
2. **A mismatch is not proof of synthetic audio.** Layer 1 flags an identity mismatch between the caller and the enrolled person. That catches cloned voices and human impersonators. It does not, by itself, prove that a voice is AI-generated.
3. **Inference is cloud-hosted.** Gnani's APIs run remotely. Audio leaves the machine for inference, and the tool requires internet access. It is a local interface with cloud-hosted inference.
4. **The sweep is partial.** This document cannot prove the absence of a similar tool, and it does not try to.
5. **Thresholds are locally calibrated.** The 0.7306-versus-0.2964 separation is a measured result on a small set of Gnani-generated samples. It is not a certified biometric evaluation across devices, accents, and channel conditions.
6. **Layer 2 is pattern-based.** Hinglish spelling varies, and ASR (automatic speech recognition) errors can cause missed flags or false positives. The transcript scan is a red-flag detector, not a semantic fraud classifier.
7. **The build analyses audio supplied to the app.** It is not a carrier-integrated live interception system. Real-time telephony integration would require a separate streaming and consent layer.

### 6.5 What would change this document

This document should be updated if any of the following appears:

- a free consumer tool that combines enrolled-voice verification with transcript scam analysis and evidence export;
- a Gnani-based project that already ships a self-test harness;
- a published evaluation showing that voiceprint mismatch alone is a reliable synthetic-audio detector;
- a change in Gnani's API terms that affects cloud inference or data handling.

---

## 7. Verification log

| Source | Fetch method | Result on 4 Nov 2026 |
|---|---|---|
| pindrop.com | Direct HTTPS | HTTP 200; product names, 300+ patents, 15+ years, 8B+ interactions, 1680% figure read |
| resemble.ai | Direct HTTPS | HTTP 200; Detect, Identity, Intelligence, executive impersonation read |
| resemble.ai/products/detect | Direct HTTPS | HTTP 200; 54 languages, 250+ models read |
| resemble.ai/resources/h1-2026-deepfake-threat-report | Direct HTTPS | HTTP 200; 821 verified attacks from 1,760 reports read |
| github.com/io-PEAK/VoxDetect | Direct HTTPS | HTTP 200; 0 stars, 4 forks, 97 commits, README claims read |
| GitHub search API, "voice clone SIH 2026" | REST API | HTTP 200; `total_count` 28 |
| GitHub search API, "voice clone detection fraud" | REST API | HTTP 200; `total_count` 55 |
| Eight SIH repositories | REST API `/repos/{owner}/{repo}` | HTTP 200 for all eight; stars recorded |
| sih-2026-problem-statements mirror | Direct HTTPS | HTTP 200; SIH26104 text read; mirror cites sih.gov.in/sih2026PS |
| asvspoof.org | Direct HTTPS | HTTP 200; challenge history read |
| arXiv 2210.02437 | Direct HTTPS | HTTP 200; title confirmed |
| nature.com/articles/s41597-026-07724-z | Direct HTTPS via DOI | HTTP 200; VISHGUARD abstract read |
| aclanthology.org/2025.acl-long.1070 | Direct HTTPS | HTTP 200; IndicSynth metadata and abstract read |
| IEEE Xplore document 11039572 | Direct HTTPS | HTTP 202, empty body; metadata confirmed via Crossref |
| doi.org/10.1201/9781003731689-104 | DOI resolution | HTTP 200; chapter title and authors confirmed |
| arxiv.org/abs/2505.00579 | Direct HTTPS | HTTP 200; survey title confirmed |
| Crossref, Emerald survey | REST API | Match found; DOI 10.1108/ATSIP-09-2025-0093 |
| realitydefender.com | Direct HTTPS | DNS failure (ENOTFOUND); not verified |
| heytring.com | Direct HTTPS | HTTP 200; languages, spam blocking, transcripts, own-voice cloning read |

---

*This document contains no uniqueness claims. Its conclusions are bounded by the sources listed above.*
