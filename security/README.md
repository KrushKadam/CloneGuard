# CloneGuard — Security Documentation

This folder contains the security audit artifacts for CloneGuard. The audit was performed on **9 November 2026** by read-only code review; all findings were independently re-verified against the working tree at commit `1cdeb5a` (fixes) and `8d0deb6` (UI).

## Audit Summary

| Finding | Severity | Status | Fix Commit |
|---|---|---|---|
| Generated data files tracked by git (voiceprints, incidents, caches, PDFs) | HIGH | Fixed | `1cdeb5a` |
| README instructed pasting key into PowerShell (shell history risk) | MEDIUM | Fixed | `1cdeb5a` |
| File uploads had no size limit | MEDIUM | Fixed | `1cdeb5a` |
| Sample selectbox path join without basename guard | LOW | Fixed | `1cdeb5a` |
| Voiceprint reads API key from Windows registry (HKCU\Environment) | LOW | Accepted (documented) | — |
| No requirements.txt with pinned versions | INFO | Fixed | `1cdeb5a` |

**Overall verdict:** Local-only breachability is **LOW** as of the audit date. The app runs on localhost, stores data locally, and calls Gnani cloud APIs over HTTPS. No pickle/eval/exec, no SSRF, no secrets in git history, no 0.0.0.0 binding.

## Document Index

1. [Threat Model](threat-model.md) — Assets, actors, trust boundaries, STRIDE table
2. [Attack Surface](attack-surface.md) — Per-surface exposure, controls, residual risk
3. [Secrets Policy](secrets.md) — GNANI_API_KEY handling, verification, rotation
4. [Security Checklist](security-checklist.md) — Pre-push and pre-release runnable checks
5. [Audit Report 2026-11-09](audit-2026-11-09.md) — Full findings, evidence, accepted risk

---
*Generated 9 November 2026. Part of the CloneGuard project for the Gnani AI Great Indian AI Internship Challenge.*