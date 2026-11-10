# CloneGuard — Innovation Report

**Prepared:** 4 November 2026
**Author:** team of two, Gnani AI — Great Indian AI Internship Challenge
**Document status:** Sections 1–5 and 7–10 drafted 4 November 2026. Section 6 awaits the build.

**Companion documents:**

- `docs/00_PROJECT_INDEX.md` — entry point, session rules, build order.
- `docs/01_PRIOR_ART.md` — the full sourced competitor and research sweep.
- `docs/02_POSITIONING.md` — canonical description, wording rules, the 8-feature list, demo path.
- `docs/03_REQUIREMENTS.md` — features with acceptance criteria, and the evidence table.
- `docs/04_ARCHITECTURE.md` — pipeline design, cut-off value, scoring formula.
- `docs/05_DATA_MODEL.md` — stored records and scoring inputs.

**Living document.** The build completed on 7 November 2026. Section 6 now carries the real measured results, and every section was re-checked against the shipped app: real screen names, real file names, real numbers from the Self-Test Harness, and real limitations found along the way.

**Scale, stated plainly.** This is a two-person team's working tool with measured evidence. It is not a research paper, and no new model, dataset, or benchmark is claimed.

**How this report is organised.** Section 2 states the problem, Section 3 summarises what already exists, Section 4 names the approach, Section 5 covers implementation, Section 6 holds the results (real measured results), Section 7 compares the approach with existing solutions feature by feature, Section 8 lists limitations, Section 9 sets out future work, and Section 10 lists the references. The layout is chosen so the report can grow into a research paper later: Section 9.3 shows where each part would move.

---

## 1. Title and Summary

CloneGuard is a desktop tool that checks a phone call for signs of impersonation. It compares the caller's voice fingerprint (called an embedding — a long list of numbers that describes how a voice sounds) against a stored fingerprint of the person the caller claims to be, and it scans the call's written text for Hinglish (Hindi written in English letters, mixed with English) scam phrases. It shows both pieces of evidence and one combined risk score, and leaves the final decision to a person.

What is new here is the combination and the way it is checked: a two-layer check (voice identity plus a Hinglish conversation scan) that picks the right enrolled voice from a spoken claim, together with a Self-Test Harness that attacks the tool using calls whose answers are already known and then publishes its own calibration scorecard (a report card comparing the tool's decisions with the truth).

---

## 2. Problem / Motivation

A fraudster can copy a voice from a short clip of public speech. The copy can then call a family member or an employee while sounding like someone they trust. The person receiving the call has no practical way to check, at the moment of the call, whether the voice on the line belongs to the person it claims to be. Enterprise tools exist, but they are sold to banks and call centres, not to a household or a small team. That is the gap this project works on.

The problem is validated at national scale. AICTE's Smart India Hackathon 2026 lists it as problem statement **SIH26104**, "AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks." The national listing is external evidence that the problem matters, and it also sets the bar for a submission: many teams are building against the same brief, so the difference has to come from execution and evidence rather than from the problem itself.

For a household or a small team, the practical need is narrow and specific: a way to compare an incoming caller against a trusted person you have enrolled, and to see the scam language in the conversation, without a sales call or a contract. CloneGuard answers that need as a local web page that runs on one machine and sends the analysis to Gnani's cloud services.

---

## 3. Prior Work / What Exists

This section is a short narrative. The full source-by-source sweep, with fetch dates and honest status labels for each source, lives in `docs/01_PRIOR_ART.md`; the tables are not repeated here.

**Enterprise products.** Pindrop sells an identity-trust platform for voice and video, aimed at contact centres and enterprises. Its Pulse product identifies synthetic speech in phone interactions, Passport authenticates known callers, and Protect scores fraud risk during a live interaction. Access runs through a sales conversation, not a download. Resemble AI sells multimodal deepfake detection (spotting AI-generated fakes across audio, video, and images) and an Identity API that enrolls a voice and matches later audio to the enrolled identities; its Identity documentation is marked as beta. Both are enterprise services with integrations and operating history behind them.

**Consumer products.** Tring is an Indian AI call assistant. It answers missed calls in several Indian languages including Hindi and Hinglish (Hindi written in English letters, mixed with English), blocks spam, provides live transcripts, and can answer in a clone of the user's own voice. That last feature is adjacent to this project but has the opposite purpose: it creates a consented synthetic voice rather than checking whether an incoming voice matches an enrolled person. Tring's public pages do not describe a trusted-person voiceprint check.

**Open and hackathon prototypes.** VoxDetect is an open-source project (GPL-3.0) that fuses a Wav2Vec2 deepfake classifier (Wav2Vec2 is a speech model that learns from raw audio) with prosody (voice rhythm and pitch patterns), voiceprint similarity, and call-context signals into a risk score. It is the closest open architecture to a multi-signal approach. AI Voice Guard and VIGIL are public SIH 2026 prototypes: each combines speaker verification or anti-spoofing with a conversation-threat layer. AI Voice Guard mixes acoustic and prosodic anomaly detection, a speaker-vector comparison, and a contextual risk engine into a simulated prevention demo. VIGIL runs an anti-spoofing model over audio and a conversation-threat analyser over the transcript.

**Research.** The field has standard references. The ASVspoof challenge series has run since 2015 as an agreed test for detecting spoofed and synthetic speech, with published metrics such as the equal error rate (a point where false accepts and false rejects are equal). The tandem detection cost function (t-DCF) is a combined measure of speaker-verification and spoof-detection errors. Indian-language speech and synthetic-speech datasets exist as benchmarks (a benchmark is a standard test dataset the field agrees on). Section 10 lists the specific works with their sources.

**What is missing for this use case.** The commercial platforms cover authentication and synthetic-audio detection, but they are aimed at large organisations and reached through sales. Tring shows multilingual consumer call handling but does not verify a claimed identity against an enrolled voice. The open prototypes combine speaker checks with context or conversation analysis, but the public pages reviewed do not advertise a built-in Hinglish scam-call generator, a self-test calibration step, or a per-check PDF incident report. A partial search cannot prove that any feature is absent from the market, and no such claim is made here.

Put simply: the commercial platforms overlap on authentication and synthetic-audio detection; Tring shows multilingual consumer call handling; the public repositories combine speaker verification with contextual assessment. CloneGuard implements these as a simplified desktop workflow — trusted-person voice similarity, transcript-based scam detection, explainable risk assessment, and incident reporting — with a self-test calibration harness, built on Gnani's cloud speech APIs.

---

## 4. My Approach — The Novel Part

The approach has a name and two halves, plus a testing loop.

### 4.1 Two-layer verification

**Layer 1 — voice identity.** The caller's audio is turned into an embedding, and that embedding is compared with the stored embedding of the person the caller claims to be, using cosine similarity (a 0-to-1 score where 1 means the two voices are identical). This catches a caller whose voice does not belong to the person they claim to be — whether that caller is a machine clone or a human impersonator. It does not, on its own, show that the audio was machine-made.

**Layer 2 — Hinglish conversation scan.** The call is transcribed (turned into written text), and the text is scanned for Hinglish scam patterns: urgency and time pressure, OTP (one-time password) and bank-detail requests, authority impersonation, threats, emotional manipulation, and deceptive calls to action. The scan returns a list of matched phrases with their category and severity, not a single yes-or-no.

The two results become one composite score (a single combined number) and one plain-language verdict. Both layers stay visible, so a person can see why the score landed where it did.

### 4.2 Claimed-identity multi-voiceprint selection

The app can store several trusted voiceprints — for example "Papa", "Mummy", or "CEO". When the text contains a claim such as "Main Papa bol raha hoon" ("I am Papa speaking") or "CEO bol raha hoon", the app works out which person is being claimed and compares the caller against that person's fingerprint instead of a generic one. A claim that names no enrolled person is reported, and the app falls back to the default enrolled voice and says so on screen.

### 4.3 Self-Test Harness

The tool attacks itself. One click generates a battery of calls — a mix of scam calls and genuine calls, each with a known answer — runs every one through the same pipeline a normal check uses, and compares the tool's decisions with the truth. The output is a calibration scorecard: how many scam calls were caught, how many genuine calls passed, and which scenario was handled worst. The test path and the demo path are the same path, which is what makes the scorecard meaningful. A failed call to a Gnani service is reported as an error and is not counted as a pass.

**What the scorecard proves, and what it does not.** A good scorecard shows that decisions were compared against known answers, that failures are visible, and that the cut-off value was chosen with evidence. It does not prove accuracy outside the test set: the scripts come from the same person who wrote the phrase list, so the test is honest about calibration but is not an independent red-team exercise.

### 4.4 Summary of research application

The table below maps each part of the tool to the published work that supports it. Reference numbers point to Section 10.

| CloneGuard component | Supporting references |
|---|---|
| Speaker embedding and voice similarity | [1], [4] |
| Speaker verification and spoofing evaluation | [2], [3] |
| Synthetic voice and deepfake detection | [3], [5], [6] |
| Indian-language audio processing | [4], [5], [6] |
| Hinglish scam and phishing phrase analysis | [8] |
| Vishing and social-engineering pattern detection | [7], [8] |

**One technical consideration, stated plainly.** Speaker similarity and synthetic-audio detection are distinct tasks. A successful imitation of an enrolled voice may still score high on identity similarity, so a voiceprint mismatch is treated as an identity-risk indicator, not as proof of synthetic speech. References [2] and [3] treat anti-spoofing (catching synthetic or replayed audio) as a separate countermeasure alongside speaker verification, which is exactly why this project keeps the two layers apart and shows both.

---

## 5. Implementation

### 5.1 Tech stack

| Part | Choice | Why |
|---|---|---|
| Interface | Streamlit (a Python library that turns a script into a web page) | A working local page with little layout code, in the same language as the existing Gnani helpers. |
| Language | Python 3 | The Gnani helpers already work; a rewrite buys nothing. |
| Audio and numbers | `wave`, `struct`, `math`, `requests` | The embeddings are small, so plain Python is enough and fewer dependencies means fewer install failures. |
| Cloud services | Gnani APIs: Prisma (speech-to-text), Timbre (text-to-speech), and Voice-Clone embeddings | The analysis runs on Gnani's cloud; the app is a local screen over those calls. |
| Storage | JSON files in a `data\` folder (JSON is a plain text format of labelled values) | One user, small numbers of records, readable and easy to back up. |
| Reports | ReportLab or fpdf2 | Keeps PDF generation (PDF is a document format that opens the same way on any machine) inside the same script. |
| Hosting | Local host, served at `localhost`, with no deployment | The contest needs a working demo, not an operated service. |

### 5.2 Pipeline data flow

One check runs in a fixed order:

1. **Audio arrives** — an uploaded WAV (an uncompressed sound file) or a generated scenario. The file is checked for existence, non-empty size, and readable audio before any cloud credit is spent.
2. **Transcript (Prisma)** — the audio becomes text.
3. **Layer 2 scan** — the text is scanned against the Hinglish pattern list; each match records its category, phrase, snippet, and severity.
4. **Voiceprint (embeddings)** — the same audio becomes a 768-number embedding and is stored so it is not recomputed.
5. **Layer 1 compare** — the caller's embedding is compared with the relevant enrolled voiceprint using cosine similarity.
6. **Claimed identity adjusts the target** — a claim phrase selects the matching enrolled person; an unclear claim falls back to the default.
7. **Composite score** — the two layer risks combine with fixed weights.
8. **Verdict** — the composite maps to one of three bands (low, caution, high) and a plain sentence. A Layer 1 mismatch does not on its own produce the word "synthetic".
9. **Spoken verdict** — Timbre reads the same verdict sentence that is on screen.
10. **Incident log** — the record is appended before the PDF step, so a report failure cannot lose the check.
11. **PDF on demand** — the stored record renders to a shareable report.

Everything above the output row runs on Gnani's cloud (remote servers reached over the internet). The screen, the incident log, and the PDF are local.

### 5.3 Key design decisions

- **Local interface with cloud inference.** The screen runs on the user's machine; the analysis runs on Gnani's cloud, so a connection is always required and audio leaves the machine for analysis.
- **Caution threshold.** The identity match cut-off starts at cosine **0.55**. The measured separation is same-speaker **0.7306** against different-speaker **0.2964**, a gap of **0.4342**; 0.55 sits inside that gap. This is an initial value, not a measured optimum — the Self-Test Harness exists to move it.
- **Explainable arithmetic.** The composite score is plain arithmetic with fixed weights, not a learned model, so anyone can recompute it from the stored record.
- **Pattern weights as starting values.** The Layer 2 phrase weights are starting values to be tuned from Self-Test data, not final settings.
- **JSON storage.** Records are written before reports and are not edited after a check completes (apart from attaching a PDF path), so history stays trustworthy.

Full detail lives in `docs/04_ARCHITECTURE.md` (pipeline, scoring formula, API reference, error handling) and `docs/05_DATA_MODEL.md` (the exact stored fields).

### 5.4 What runs locally and what runs in the cloud

| Step | Where it runs | Why |
|---|---|---|
| Screen, buttons, tables | Local machine (`localhost`) | The interface is the part a person uses. |
| Speech-to-text (Prisma) | Gnani cloud | The app calls a web service, so the audio leaves the machine for this step. |
| Voice embedding | Gnani cloud | The embedding call is remote. |
| Text-to-speech (Timbre) | Gnani cloud | The spoken verdict is generated remotely. |
| Incident log and PDF | Local machine | Records stay on the machine. |

This layout matters for the wording rules: the interface is local and the analysis is cloud-based, so the tool needs a connection, and it is described that way in every public sentence.

---

## 6. Results / Demo

**Pipeline runs end to end.** The numbers below come from the Self-Test Harness run of 7 November 2026 (run_id `run_20261107_182914_fa8e`) and the AppTest checks of the interface.

### 6.1 What is already proven

| Claim | Evidence | Status |
|---|---|---|
| The voice comparison separates speakers | Same-speaker cosine **0.7306**, different-speaker **0.2964**, separation **0.4342** (from `voiceprint_test.py`) | Proven |
| The fingerprint step is repeatable | Re-running the same audio returns identical numbers | Proven |

### 6.2 What is pending and how it will be shown

| Claim | How it will be shown | Status |
|---|---|---|
| Layer 2 catches Hinglish scam phrasing | Matched phrases listed in the app with the rule that fired | Proven — every scam scenario produced 2-8 matched phrases; battery: 7/7 scams caught |
| The claimed-identity flow selects the right voice | The app shows the detected claim and the chosen voiceprint id | Proven — claim resolver picks the target row in every scenario with a claim |
| The tool is calibrated, not just working | Scorecard: scam caught X/Y, genuine passed A/B, weakest scenario | Proven — scam caught 7/7, genuine passed 3/3, caution 0, errors 0; weakest scam: family_emergency at 75/100 |
| The full pipeline runs end to end | A passing pipeline test plus a live demo run | Proven — scam sample scored 74/100 (high), genuine sample 0/100 (low); interface served HTTP 200 on localhost |
| Evidence can leave the app | A generated PDF containing both layers and the transcript excerpt | Proven — 57,261-byte A4 PDF; text extraction confirmed verdict, limitations, timestamp and Layer-2 phrases |

### 6.3 Planned demo

The 60-second demo path — enroll, generate a scam call, run the check, run the Self-Test Harness, play the spoken verdict, open the PDF and incident log — is written out in `docs/02_POSITIONING.md`, Section 3.2, and mirrors `docs/03_REQUIREMENTS.md`, Section 7. The demo path was executed during trials; the harness scorecard is scam caught 7/7, genuine passed 3/3, caution 0, errors 0, and the result is stable across every threshold in the 0.45–0.65 sweep (each point: 7/7 and 3/3). The scorecard PDF is generated by the app's Self-test page.

---

## 7. Comparison Table

This section is where the project argues that it is an implementation and an integration, not a rebuild of the same idea. Every row is written as "an existing solution does A; CloneGuard does B," and each is at the feature level. Sources for the existing solutions are in `docs/01_PRIOR_ART.md`.

| Existing solution | What it does | What CloneGuard does differently (feature level) |
|---|---|---|
| **Pindrop** (enterprise) | Pulse identifies synthetic speech in contact-centre calls; Passport authenticates known callers; Protect scores live fraud risk. Reached through a sales conversation. | CloneGuard is a local desktop page a single person can run without a contract. It reports an identity mismatch plus scam-language evidence for a claimed trusted person, and it exports a per-check PDF. |
| **Resemble AI** (enterprise SaaS) | Detect returns a verdict and explanation for audio, video, and images; the Identity API enrolls a voice and matches incoming audio to enrolled identities (documented as beta). | CloneGuard composes three Gnani APIs into one local verdict and adds a built-in Hinglish scam-call generator, a self-test scorecard, and PDF incident reports. |
| **Tring** (consumer, India) | An AI call assistant that answers calls in Indian languages including Hinglish, blocks spam, transcribes live, and can answer in the user's own cloned voice. | CloneGuard checks whether a caller matches an enrolled trusted person. Tring creates a consented synthetic voice for answering; CloneGuard verifies a claimed identity against a stored voiceprint and scans the transcript for scam patterns. |
| **VoxDetect** (open prototype) | Fuses a Wav2Vec2 deepfake classifier with prosody, voiceprint similarity, and call-context signals into a risk score. Closest open multi-signal architecture. | CloneGuard adds a Hinglish scam layer and generator, a Self-Test calibration harness, PDF evidence reports, and a claimed-identity multi-voiceprint flow, on a cloud speech API rather than a local model. |
| **AI Voice Guard** (SIH 2026 prototype) | Combines acoustic and prosodic anomaly detection, a speaker-vector comparison, and a contextual risk engine into a simulated prevention demo with action bands. | CloneGuard adds a self-test calibration harness, a Hinglish scam-call generator, PDF incident reports, and a claimed-identity multi-voiceprint flow built on Gnani's embeddings, Prisma, and Timbre. |
| **VIGIL** (SIH 2026 prototype) | Runs an anti-spoofing model over audio plus a conversation-threat analyser over the transcript, with browser WebRTC monitoring and a detection history. | CloneGuard adds a self-test calibration harness that publishes its own scorecard, a Hinglish scam-call generator, PDF evidence reports, and claimed-identity voiceprint selection. |
| **Gnani AI** (Prisma and Timbre) | Indian-language speech technology: speech-to-text, code-mixed transcription, telephony processing, and text-to-speech. | Gnani is the foundation this project builds on, not a fraud-detection app. CloneGuard composes three Gnani APIs into one identity-and-language risk verdict. |

**How to read this table.** The rows describe what each product's public pages advertise and what CloneGuard adds at the feature level. They are not claims that any feature is absent everywhere. When a judge asks "hasn't this been done?", the honest answer is: partly, across several products and prototypes — and this implementation is complete, measurable, and explainable for a household or small team, with a self-test loop and evidence output.

---

## 8. Limitations

Four limitations are documented across the project and are stated wherever the tool is described. They are not defects to hide; they are the boundary of what the evidence supports, and each appears in the app, the PDF report, and the public descriptions.

1. **A perfect clone of the enrolled voice passes Layer 1.** If the copied audio is clean and the words are ordinary, the fingerprint match will look like the real person. Matching an identity is not proof that the audio is genuine.
2. **A voiceprint mismatch is an identity-risk indicator, not proof of synthetic audio.** Layer 1 flags a mismatch between the caller and the enrolled voice. That catches cloned voices and human impersonators alike. It does not, on its own, show that the audio was machine-generated.
3. **The analysis needs an internet connection.** Inference runs on Gnani's cloud, so audio leaves the machine for analysis, and the app does not work without a connection. It is a local interface with cloud inference.
4. **A partial search cannot prove absence.** "No scam patterns found" means the scan did not match its phrase list. It does not mean the call is safe, and the app must not say that it does.

Three further scope notes bound what the evidence supports:

- **The sample set is small and self-generated.** The 0.7306-against-0.2964 separation is a measured result on a small set of Gnani-generated samples. It is not a certified biometric evaluation (a formal test of body-based identity measurement) across devices, accents, and channel conditions.
- **The pattern weights are starting values.** The Layer 2 weights are placeholders to be tuned from Self-Test data, not fixed settings.
- **Threshold calibrated at 0.55.** Sweep across 0.45–0.65 showed 7/7 scam caught and 3/3 genuine passed at every point; caution 0, errors 0.

**Demo rule.** All demo and test audio is generated with Timbre. No real victim recording and no real scam call is used without consent. The generated calls test the pipeline against known scripts, not against real fraudsters, and the app analyses audio supplied to it rather than intercepting live phone calls.

---

## 9. Future Work

The roadmap below is written now, so the report can grow into a research paper later without a rewrite.

### 9.1 Product phases

| Phase | What it adds | When |
|---|---|---|
| Phase 2 — desktop background monitor | A small background process that watches audio the user supplies and raises the same two-layer signal without re-opening the app for each check. | After the build, if time allows. |
| Phase 3 — Android and real-time | A mobile front end and a streaming path, which would need a separate consent and telephony layer. | After the challenge. |

The build today analyses audio supplied to it and does not intercept ordinary phone calls.

### 9.2 Research upgrades

These are the steps that would move the work from a working tool to a research-grade evaluation.

- **Public spoofing benchmarks.** Evaluate the approach on ASVspoof-style test sets (standard agreed datasets) instead of a self-generated set.
- **Cross-language testing.** Test on Indic synthetic-speech datasets such as IndicSynth, which covers synthetic speech across Indian languages.
- **Larger genuine and scam sample sets.** Replace the small self-generated set with a broader, more varied one.
- **Pattern-weight tuning.** Use the Self-Test data to move the Layer 2 weights and the identity cut-off from starting values to measured ones.
- **Baseline comparison.** Compare against baseline models (for example a CNN-Transformer deepfake detector on Indian-language audio) to place the embedding-based identity check in context.

### 9.3 How the sections map onto a paper

| Report section | Future paper section |
|---|---|
| 2 and 3 | Introduction and Literature Review |
| 4 and 5 | Methodology |
| 6 | Results |
| 7 and 8 | Discussion |
| 9 | Conclusion |
| 1 | Abstract |

---

## 10. References

Each entry gives a one-line note on what the work establishes and why it matters to CloneGuard, with the exact DOI or URL preserved. Verification status is marked per entry. Verification was done by fetching the source on 4 November 2026 unless noted.

**Research references**

1. Desplanques, B., Thienpondt, J., & Demuynck, K. (2020). *ECAPA-TDNN: Emphasized Channel Attention, Propagation and Aggregation in TDNN Based Speaker Verification.* INTERSPEECH 2020, pp. 3830–3834. DOI: https://doi.org/10.21437/Interspeech.2020-2650
   *Establishes:* a well-known speaker-embedding architecture that uses channel attention and aggregation. *Relevance:* background for how speaker embeddings work. It is not evidence that Gnani uses this architecture. — **Verified (4 November 2026)**.

2. Kinnunen, T., Delgado, H., Evans, N., Lee, K. A., Vestman, V., Nautsch, A., Todisco, M., Wang, X., Sahidullah, M., Yamagishi, J., & Reynolds, D. A. (2020). *Tandem Assessment of Spoofing Countermeasures and Automatic Speaker Verification: Fundamentals.* IEEE/ACM TASLP, Vol. 28, pp. 2195–2210. DOI: https://doi.org/10.1109/TASLP.2020.3009494
   *Establishes:* the tandem detection cost function (t-DCF), which evaluates speaker verification and spoof detection together. *Relevance:* explains why identity verification and synthetic-audio detection are separate but complementary, and frames false-accept and false-reject thinking. — **Verified (4 November 2026)**.

3. Yamagishi, J., Wang, X., Todisco, M., Sahidullah, M., Patino, J., Nautsch, A., Liu, X., Lee, K. A., Kinnunen, T., Evans, N., & Delgado, H. (2021). *ASVspoof 2021: accelerating progress in spoofed and deepfake speech detection.* 2021 Edition of the ASVspoof Challenge, pp. 47–54. DOI: https://doi.org/10.21437/ASVSPOOF.2021-8
   *Establishes:* challenge datasets, protocols, and baselines for replay, spoof, and deepfake detection, including the effect of compression and transmission. *Relevance:* an evaluation framework, and a reminder that varied audio quality and telephonic conditions matter. — **Verified (4 November 2026)**.

4. Javed, T., Bhogale, K., Raman, A., Kumar, P., Kunchukuttan, A., & Khapra, M. M. (2023). *IndicSUPERB: A Speech Processing Universal Performance Benchmark for Indian Languages.* Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 37, No. 11, pp. 12942–12950. DOI: https://doi.org/10.1609/aaai.v37i11.26521
   *Establishes:* a benchmark covering 12 Indian languages, 1,684 hours from 1,218 contributors across 203 districts, with tasks including speech recognition and speaker identification. *Relevance:* an Indian-language evaluation foundation for transcription and voice-similarity reliability. (Note: the project's earlier shorthand "IndICUPERB" is this same paper; the published title is IndicSUPERB.) — **Verified (4 November 2026)**.

5. Sharma, B., Ekbote, N., & Gupta, A. (2025). *IndicSynth: Evaluation of Synthetic Speech Across Indian Linguistic Accents and Code-Switching.* ACL 2025 (Long Papers), pp. 22037–22060. DOI: https://doi.org/10.18653/v1/2025.acl-long.1070
   *Establishes:* a multilingual synthetic-speech dataset of about 4,000 hours, 989 speakers, and 12 Indian languages, and studies linguistic bias in synthetic-speech detection. *Relevance:* a future cross-language testing resource. — **Verified 4 November 2026 (carried forward from the verification recorded in `01_PRIOR_ART.md`; not re-fetched in this pass)**.

6. Gaikawad, S., & Ghosh, S. (2025). *A Robust and Lightweight CNN-Transformer Model for Audio Deepfake Detection in Indian Languages.* ISPCC 2025, pp. 382–387. DOI: https://doi.org/10.1109/ISPCC66872.2025.11039572
   *Establishes:* a hybrid CNN-Transformer on Mel/LFCC/Wav2Vec features for Hindi, Marathi, Tamil, Telugu, Malayalam, and Kannada; the publisher abstract reports 98.07% test accuracy on their own evaluation dataset. *Relevance:* a reference for future improvement beyond embedding-based identity comparison. — **Verified 4 November 2026 (carried forward; not re-fetched in this pass)**.

7. Hmimou, Y., Tabaa, M., Khiat, A., & Hidila, Z. (2026). *A Multilingual Behavioral Speech Dataset for Vishing and Social Engineering Detection (VISHGUARD).* Scientific Data, Vol. 13, Article 1456, 29 June 2026. DOI: https://doi.org/10.1038/s41597-026-07724-z
   *Establishes:* a dataset of 3,000 simulated telephone conversations (English, French, Modern Standard Arabic), fraudulent and legitimate, annotated for persuasion strategies, emotional tone, pauses, and interruptions. *Relevance:* a reference for social-engineering indicators (urgency, threats, authority pressure). It contains no Indian languages. — **Verified 4 November 2026 (carried forward; not re-fetched in this pass)**.

8. Meena, D., Dayanvita, Singh, M., Shweta, & Singh, J. *Hinglish Text Phishing Detection Model Using Machine Learning Algorithms.* IGDTUW Research Showcase, *Compendium of Abstracts: Future and Technology*, December 2024, abstract 43, p. 44. Source: https://www.igdtuw.ac.in/IGDTUW/uploads/919646825.pdf
   *Establishes:* machine-learning and rule-based detection of phishing in Hinglish text, using keyword and fuzzy matching with negation handling, classifiers (Naïve Bayes, k-nearest neighbours, support vector machines, random forest, gradient boosting), and a fine-tuned BERT model, with urgency, emotional, and call-to-action cues. *Relevance:* a direct precedent for treating Hinglish text patterns as a fraud signal in the transcript-analysis layer. *Qualification:* this is a university research-showcase abstract, not a separately verified peer-reviewed paper, and detailed metrics are not in the accessible abstract. — **Verified (4 November 2026): the PDF loads (HTTP 200, application/pdf, about 1.69 MB, 83 pages) and abstract 43 was read, confirming the title, authors, venue, and December 2024 date. The page number 44 is the source material's citation; the abstract itself is numbered 43.**

**Prior-art and vendor sources**

These support Section 7 and the narrative in Section 3. The full sweep, with the fetch method and result for each, is in `docs/01_PRIOR_ART.md`, Section 7.

| Source | URL | Verification |
|---|---|---|
| Pindrop — Pulse for Contact Centers | https://www.pindrop.com/pulse-for-contact-centers | Verified (4 November 2026): page loaded; products and synthetic-speech detection confirmed. |
| Resemble AI — Detect | https://www.resemble.ai/products/detect | Verified (4 November 2026): page loaded; multimodal detection and Identity product confirmed. |
| Tring — AI Call Assistant | https://heytring.com/ | Verified (4 November 2026): page loaded; Indian-language call handling and own-voice cloning confirmed. |
| VoxDetect | https://github.com/io-PEAK/VoxDetect | Verified (4 November 2026): repository loaded; GPL-3.0, multi-signal fusion README, 0 stars and 4 forks confirmed. |
| AI Voice Guard | https://github.com/Dhaksin-Kaarthick/AI-VOICE-GUARD | Verified (4 November 2026): repository loaded; SIH26104 prototype with speaker and context risk scoring confirmed. GitHub API: created and last pushed 4 September 2026, 0 stars, 1 commit. |
| VIGIL | https://github.com/AkaiAyu/VIGIL | Verified (4 November 2026): repository loaded; anti-spoofing model plus conversation-threat analysis confirmed. GitHub API: created 14 September 2026, last pushed 23 September 2026, 0 stars, 5 commits. |
| Gnani AI — Prisma and Timbre | https://www.gnani.ai/resources/prisma-v3 | Verified (4 November 2026): Indian-language speech technology confirmed as the foundation, not a fraud-detection app. |

---

*Prepared 4 November 2026. This is a living document: Section 6 will be completed after the build, and every section will then be re-checked against the finished app. No result is stated anywhere in this report that a completed run has not produced.*
