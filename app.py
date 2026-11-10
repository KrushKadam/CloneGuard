"""CloneGuard — Streamlit interface.

Start it from the project root:

    streamlit run app.py

The interface runs locally on this machine. The analysis (transcription,
voice fingerprints, text to speech) runs on Gnani's cloud APIs, so the app
needs an internet connection. A check on an audio file that is already cached
makes no API calls.
"""

import datetime as dt
import glob
import json
import os
import re
import sys
import tempfile
import wave

import requests
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
import gnani
from engine import layer1 as layer1_mod
from engine import pipeline
from engine import score as score_mod

TEMP_DIR = os.path.join(tempfile.gettempdir(), "cloneguard_ui")

PAGES = [
    "Check a call",
    "Spoken verdict",
    "Enroll a voice",
    "Self-test",
    "Incident log",
]

VERDICT_VOICES = ["Nalini", "Deepak"]

TARGET_MARK = "target"

LIMITATIONS = [
    "A perfect clone of the enrolled voice passes the voice match. A match is "
    "a weak signal, not proof that the audio is genuine.",
    "A mismatch is not proof of synthetic audio. Layer 1 flags an identity "
    "mismatch, and a human impersonator produces the same flag.",
    "The analysis runs on Gnani's cloud APIs. Audio leaves this machine and "
    "the app needs an internet connection.",
    '"No patterns matched" means the phrase list did not match. It does not '
    "mean the call is safe.",
]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def api_key_present():
    return bool((os.environ.get("GNANI_API_KEY") or "").strip())


def temp_path(suffix=".wav"):
    os.makedirs(TEMP_DIR, exist_ok=True)
    handle, path = tempfile.mkstemp(prefix="cg_ui_", suffix=suffix, dir=TEMP_DIR)
    os.close(handle)
    return path


def readable_error(exc):
    """Turn an exception into the short message style from the docs."""
    text = str(exc).strip() or exc.__class__.__name__
    low = text.lower()

    if isinstance(exc, FileNotFoundError):
        return "That audio file could not be found. Pick it again."
    if isinstance(exc, ValueError) and ("empty" in low or "directory" in low):
        return "That file is empty or not readable audio. Upload a WAV."
    if "gnani_api_key" in low:
        return "Set the environment variable GNANI_API_KEY and restart the app."
    if isinstance(exc, requests.exceptions.Timeout) or "timed out" in low or "timeout" in low:
        return "The request took too long and was stopped. Try again in a moment."
    if isinstance(exc, requests.exceptions.ConnectionError) or any(
        word in low
        for word in (
            "connection",
            "max retries",
            "getaddrinfo",
            "name or service",
            "cannot reach",
            "ssl",
            "proxy",
        )
    ):
        return "Cannot reach Gnani. Check your connection and try again."
    if (
        "401" in text
        or "403" in text
        or "unauthorized" in low
        or "forbidden" in low
        or "api key" in low
    ):
        return "API key rejected. Check GNANI_API_KEY."
    if "429" in text or "rate limit" in low or "quota" in low or "credit" in low:
        return "Credit limit reached or rate limited. Check app.gnani.ai, Usage page."
    code = re.search(r"\b(5\d\d)\b", text)
    if code:
        return "Gnani had a problem (code %s). Try again in a moment." % code.group(1)
    return "The request could not finish: " + (text[:240] + ("..." if len(text) > 240 else ""))


def save_upload(uploaded):
    """Write an uploaded WAV to a temp file after a header check."""
    data = uploaded.getvalue() if hasattr(uploaded, "getvalue") else uploaded.read()
    if not data:
        raise ValueError("audio file is empty")
    if len(data) > 25 * 1024 * 1024:
        raise ValueError("File is larger than 25 MB. Use a shorter recording.")
    path = temp_path()
    with open(path, "wb") as handle:
        handle.write(data)
    try:
        with wave.open(path, "rb") as reader:
            reader.getnframes()
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise ValueError("audio file is empty or not readable audio")
    return path


def sample_files():
    return sorted(
        os.path.basename(path)
        for path in glob.glob(os.path.join(config.SAMPLES_DIR, "gc_*.wav"))
    )


def short(text, width=160):
    value = " ".join(str(text or "").split())
    if len(value) <= width:
        return value
    return value[: width - 3].rstrip() + "..."


def parse_time(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def show_time(value):
    parsed = parse_time(value)
    if parsed is None:
        return str(value or "")
    return parsed.strftime("%d %b %Y, %H:%M")


def band_label(band):
    return {"low": "Low risk", "caution": "Caution", "high": "High risk"}.get(
        band, str(band or "-")
    )


def ordinal_percent(value):
    return "-" if value is None else "%.4f" % float(value)


# ---------------------------------------------------------------------------
# Shared chrome
# ---------------------------------------------------------------------------

def sidebar():
    st.sidebar.title("CloneGuard")
    st.sidebar.caption("Identity and language risk check for a supplied call recording.")

    st.sidebar.caption("Choose a page:")
    if "page" not in st.session_state:
        st.session_state.page = PAGES[0]

    for i, page_name in enumerate(PAGES):
        is_active = st.session_state.page == page_name
        st.sidebar.button(
            page_name,
            key="nav_%d" % i,
            on_click=lambda p=page_name: st.session_state.update({"page": p}),
            type="primary" if is_active else "secondary",
            use_container_width=True,
        )

    st.sidebar.divider()
    try:
        enrolled = len(layer1_mod.load_voiceprints())
    except Exception:
        enrolled = 0
    st.sidebar.write("Voiceprints enrolled: **%d**" % enrolled)
    if api_key_present():
        st.sidebar.success("GNANI_API_KEY found")
    else:
        st.sidebar.error("GNANI_API_KEY missing")
    st.sidebar.caption("Interface local, analysis on Gnani's cloud APIs.")
    return st.session_state.page


def render_footer():
    st.divider()
    st.caption(
        "Interface runs locally on this machine (localhost). Analysis runs on "
        "Gnani's cloud APIs and needs an internet connection."
    )
    with st.expander("Limitations"):
        for item in LIMITATIONS:
            st.markdown("- " + item)
        st.caption(
            "The verdict is a risk signal with evidence, not an automatic fraud "
            "determination. A human makes the final decision."
        )


# ---------------------------------------------------------------------------
# Section 1: check a call
# ---------------------------------------------------------------------------

def layer1_panel(result):
    st.markdown("#### Layer 1: voiceprint comparison")
    layer1 = result.get("layer1") or {}
    comparisons = layer1.get("comparisons") or []
    threshold = layer1.get("threshold", config.THRESHOLD)

    st.caption(
        "Cosine similarity is a 0-to-1 score where 1 means the two voices are "
        "identical. The cut-off (threshold) is %.2f." % float(threshold)
    )

    if comparisons:
        rows = []
        for row in comparisons:
            rows.append(
                {
                    "Voiceprint": row.get("name") or "-",
                    "Role": row.get("role") or "-",
                    "Cosine": ordinal_percent(row.get("cosine")),
                    "Threshold": "%.2f" % float(row.get("threshold", threshold)),
                    "Result": row.get("verdict") or "-",
                    "Target": TARGET_MARK if row.get("target") else "",
                }
            )
        st.dataframe(rows, hide_index=True)
        st.caption(
            "The row marked target is the voiceprint the identity claim resolved to."
        )
    else:
        st.info(
            "No voiceprints are enrolled, so Layer 1 was not scored. Enroll a voice in the Enroll section."
        )

    claim = result.get("claim") or {}
    note = claim.get("note")
    if note:
        st.markdown("**Claim:** " + note)
    st.markdown("**Layer 1 result:** " + str(layer1.get("label") or "-"))


def layer2_panel(result):
    st.markdown("#### Layer 2: Hinglish scam-pattern scan")
    hits = (result.get("layer2") or {}).get("hits") or []

    if hits:
        rows = []
        for hit in hits:
            rows.append(
                {
                    "Category": hit.get("category") or "-",
                    "Matched phrase": hit.get("matched_phrase") or "-",
                    "Snippet": hit.get("transcript_snippet") or "",
                    "Severity": hit.get("severity") or "-",
                    "Weight": "%.2f" % float(hit.get("weight") or 0.0),
                }
            )
        st.dataframe(rows, hide_index=True)
    else:
        st.info("No patterns matched — this does not mean the call is safe.")


def composite_panel(result):
    st.markdown("#### Composite result")
    composite = result.get("composite")
    band = result.get("band")
    layer1 = result.get("layer1") or {}
    hits = (result.get("layer2") or {}).get("hits") or []

    left, middle, right = st.columns(3)
    left.metric("Composite risk", "%s / 100" % composite)
    middle.metric("Band", band_label(band))
    right.metric("Layer 1 cosine", ordinal_percent(layer1.get("best_cosine")))

    sentence = result.get("verdict_sentence") or ""
    if band == "high":
        st.error(sentence)
    elif band == "caution":
        st.warning(sentence)
    else:
        st.info(sentence)

    with st.expander("How this score was built"):
        l1_risk = score_mod.layer1_risk(layer1.get("best_cosine"))
        l2_risk = score_mod.layer2_risk(hits)
        st.write(
            "Layer 1 risk: %s (weight %.2f). Layer 2 risk: %.4f (weight %.2f)."
            % (
                "-" if l1_risk is None else "%.4f" % l1_risk,
                config.W_L1,
                l2_risk,
                config.W_L2,
            )
        )
        st.caption(
            "Layer 2 risk is the sum of the matched phrase weights divided by "
            "%.2f, capped at 1.0. When Layer 1 has no comparable voiceprint, "
            "the Layer 2 risk alone is rescaled to 0-100." % config.LAYER2_DIVISOR
        )
        notes = result.get("notes") or []
        if notes:
            st.markdown("**Notes from the engine:**")
            for note in notes:
                st.markdown("- " + str(note))

    if result.get("transcript"):
        with st.expander("Transcript (Prisma)"):
            st.write(result["transcript"])


def find_incident(record_id):
    """The stored row in data\\incidents.json for this check, or None."""
    if not record_id:
        return None
    for entry in reversed(load_incidents()):
        if entry.get("id") == record_id:
            return entry
    return None


def evidence_panel(result):
    """Prepare the PDF evidence report for the stored check and offer it."""
    try:
        record = find_incident(result.get("record_id"))
    except Exception:
        record = None
    if record is None:
        return

    st.markdown("#### Evidence report")
    st.caption(
        "One PDF built from the stored record. Making it runs no new analysis "
        "and spends no Gnani calls."
    )

    if st.button("Prepare evidence report (PDF)", key="evidence_prepare"):
        try:
            from reports import incident_pdf

            path = incident_pdf.render_incident_pdf(record)
            with open(path, "rb") as handle:
                data = handle.read()
            st.session_state["evidence_pdf"] = {
                "record_id": record.get("id"),
                "name": os.path.basename(path),
                "path": path,
                "data": data,
            }
        except Exception:
            st.error(
                "Report could not be saved. The check is still in the incident log."
            )
            return

    bundle = st.session_state.get("evidence_pdf")
    if bundle and bundle.get("record_id") == record.get("id"):
        st.download_button(
            "Download evidence report (PDF)",
            data=bundle["data"],
            file_name=bundle["name"],
            mime="application/pdf",
            key="evidence_download",
        )
        st.caption("Saved at %s" % bundle["path"])
    elif bundle:
        st.caption(
            "Another check was exported last. Prepare the report again for this check."
        )


def render_check_page():
    st.subheader("Check a call")
    st.caption(
        "Upload a recording and see if the caller's voice matches an enrolled person, "
        "and find any scam phrases the caller used. This page runs about 2 calls to "
        "Gnani's APIs (transcription plus voice identity check)."
    )

    if api_key_present():
        st.caption(
            "Audio that was already processed on this machine is reused without "
            "a new API call."
        )
    else:
        st.warning(
            "GNANI_API_KEY is not set. Cached files still run; a new file will "
            "fail when it calls the API."
        )

    left, right = st.columns(2)
    with left:
        uploaded = st.file_uploader(
            "Upload a call recording (WAV) from your device", type=["wav"], key="check_upload", max_upload_size=25
        )
    with right:
        names = sample_files()
        picked = st.selectbox(
            "Or pick a sample file from samples\\",
            options=[""] + names,
            format_func=lambda value: value or "Choose a sample file",
            key="check_sample",
        )

    if uploaded is not None and picked:
        st.caption("Both are set, so the uploaded file is used.")

    if st.button("Run the check", type="primary"):
        path = None
        try:
            if uploaded is not None:
                path = save_upload(uploaded)
            elif picked:
                picked = os.path.basename(picked)
                path = os.path.join(config.SAMPLES_DIR, picked)
                if not os.path.exists(path):
                    raise FileNotFoundError(path)
            else:
                raise ValueError("Choose a WAV to check, or pick a sample file.")

            result = pipeline.run_check(path)

            record_id = None
            try:
                entry = pipeline.save_record(result)
                record_id = entry.get("id")
            except Exception as save_exc:
                st.warning(
                    "The check finished, but the incident log could not be "
                    "written: " + readable_error(save_exc)
                )

            result["record_id"] = record_id
            st.session_state["check_result"] = result
        except Exception as exc:
            st.error(readable_error(exc))

    result = st.session_state.get("check_result")

    if result:
        audio_rel = result.get("audio_path") or ""
        audio_abs = os.path.join(ROOT, audio_rel.replace("/", os.sep))
        if audio_rel and os.path.exists(audio_abs):
            with st.expander("Caller audio"):
                st.audio(audio_abs, format="audio/wav")

        st.divider()
        layer1_panel(result)
        st.divider()
        layer2_panel(result)
        st.divider()
        composite_panel(result)

        if result.get("record_id"):
            st.caption("Saved to the incident log as %s." % result["record_id"])
            st.divider()
            evidence_panel(result)
    else:
        st.divider()
        st.markdown("#### Layer 1: voiceprint comparison")
        st.caption("Run a check to see the comparison rows.")
        st.divider()
        st.markdown("#### Layer 2: Hinglish scam-pattern scan")
        st.caption("Run a check to see the matched phrases.")
        st.divider()
        st.markdown("#### Composite result")
        st.caption("Run a check to see the score and the verdict.")


# ---------------------------------------------------------------------------
# Section 2: spoken verdict
# ---------------------------------------------------------------------------

def render_spoken_page():
    st.subheader("Spoken verdict")
    st.caption("Hear the verdict read aloud. Uses one Gnani API call to speak the text.")

    result = st.session_state.get("check_result")
    if not result:
        st.info("Run a check, then the verdict can be spoken here.")
        st.markdown("**No verdict yet.** Open Check a call and run a check.")
        st.button(
            "Open Check a call",
            key="cta_open_check",
            on_click=lambda: st.session_state.update({"page": "Check a call"}),
        )
        return

    sentence = result.get("verdict_sentence") or ""
    st.markdown("**Verdict on screen:** " + sentence)

    left, right = st.columns([1, 1])
    with left:
        voice = st.selectbox("Voice with Timbre", VERDICT_VOICES, key="verdict_voice")
    with right:
        play = st.button("Play the verdict aloud", type="primary")

    spoken = st.session_state.get("spoken_verdict")
    if play:
        path = temp_path()
        try:
            gnani.text_to_speech(sentence, voice=voice, out=path)
            if not os.path.exists(path) or os.path.getsize(path) <= 0:
                raise RuntimeError("empty audio returned by Timbre")
            st.session_state["spoken_verdict"] = {
                "text": sentence,
                "voice": voice,
                "path": path,
            }
            spoken = st.session_state["spoken_verdict"]
        except Exception as exc:
            try:
                os.remove(path)
            except OSError:
                pass
            st.error("spoken verdict unavailable")
            st.caption(readable_error(exc))

    spoken = st.session_state.get("spoken_verdict")
    if spoken and spoken.get("text") == sentence and spoken.get("voice") == voice:
        st.caption("Spoken text: " + spoken["text"])
        if os.path.exists(spoken.get("path") or ""):
            st.audio(spoken["path"], format="audio/wav")
        else:
            st.info("The last spoken file is no longer on disk. Play it again.")
    elif spoken:
        st.caption("The voice or verdict changed. Play again to hear the current verdict.")

    st.caption("The text verdict stays on screen whether or not the speech call worked.")


# ---------------------------------------------------------------------------
# Section 3: enrollment
# ---------------------------------------------------------------------------

def render_enroll_page():
    st.subheader("Enroll a voice")
    flash = st.session_state.pop("enroll_flash", None)
    if flash:
        st.success(flash)
    st.caption(
        "Create a voiceprint so the check can compare the caller to a trusted person. "
        "Voiceprint is a 768-number feature file of how a person sounds. A new audio "
        "file costs one embedding call; audio already cached costs none."
    )

    left, right = st.columns(2)
    with left:
        name = st.text_input("Name for this person", placeholder="Nalini", key="enroll_name")
    with right:
        role = st.text_input("Role in the context", placeholder="Papa", key="enroll_role")

    st.caption(
        "The role is matched against claim phrases in the transcript. The engine "
        "has claim lookups for Papa, Mummy, and CEO. Re-enrolling the same role "
        "replaces that voiceprint."
    )

    uploaded = st.file_uploader(
        "Voice sample (WAV file)",
        type=["wav"],
        key="enroll_upload",
        max_upload_size=25,
    )

    if st.button("Enroll or replace voiceprint", type="primary"):
        try:
            if not (name or "").strip():
                raise ValueError("Type a name before enrolling.")
            if not (role or "").strip():
                raise ValueError("Type a role before enrolling.")
            if uploaded is None:
                raise ValueError("Upload a WAV voice sample before enrolling.")
            path = save_upload(uploaded)
            record = layer1_mod.enroll(path, name.strip(), role.strip())
            st.session_state["enroll_flash"] = (
                "Enrolled %s as %s (voiceprint %s)."
                % (record.get("name"), record.get("role"), record.get("id"))
            )
            st.rerun()
        except Exception as exc:
            st.error(readable_error(exc))

    st.divider()
    st.markdown("#### Enrolled voiceprints")

    records = layer1_mod.load_voiceprints()
    if records:
        rows = []
        for record in records:
            rows.append(
                {
                    "Name": record.get("name") or "-",
                    "Role": record.get("role") or "-",
                    "Date": show_time(record.get("created_at")),
                    "Source": record.get("source_path") or "-",
                }
            )
        st.dataframe(rows, hide_index=True)

        labels = {
            "%s (%s) [%s]"
            % (
                record.get("name") or "unnamed",
                record.get("role") or "no role",
                record.get("id") or "-",
            ): record.get("id")
            for record in records
        }
        chosen = st.selectbox("Voiceprint to remove", list(labels.keys()))
        if st.button("Remove voiceprint"):
            removed = layer1_mod.remove_voiceprint(labels[chosen])
            if removed:
                st.session_state["enroll_flash"] = "Removed %s (%s)." % (
                    removed.get("name"),
                    removed.get("role"),
                )
                st.rerun()
            else:
                st.error("That voiceprint is no longer in the list. Refresh and try again.")
    else:
        st.info("No voiceprints enrolled yet. Enroll one above before running a check.")


# ---------------------------------------------------------------------------
# Section 4: self-test
# ---------------------------------------------------------------------------

def _scorecard_tables(run):
    metrics = run.get("metrics") or {}

    columns = st.columns(4)
    columns[0].metric("Scam caught", metrics.get("scam_caught") or "-")
    columns[1].metric("Genuine passed", metrics.get("genuine_passed") or "-")
    columns[2].metric("Caution", metrics.get("caution_count", 0))
    columns[3].metric("Errors", metrics.get("errors", 0))

    st.write("**Weakest scenario:** " + str(metrics.get("weakest") or "n/a"))
    st.caption(run.get("honesty_line") or "")

    st.markdown("##### Threshold sweep")
    sweep_rows = []
    for row in run.get("sweep") or []:
        sweep_rows.append(
            {
                "Threshold": "%.2f" % float(row.get("threshold", 0)),
                "Scam caught": str(row.get("scam_caught", "-")),
                "Genuine passed": str(row.get("genuine_passed", "-")),
                "Caution": row.get("caution_count", 0),
                "Errors": row.get("errors", 0),
            }
        )
    if sweep_rows:
        st.dataframe(sweep_rows, hide_index=True)
    else:
        st.info("No threshold sweep in this run.")

    hard_rows = []
    for row in run.get("scenarios") or []:
        if not row.get("hard_case"):
            continue
        hard_rows.append(
            {
                "Scenario": row.get("scenario_id"),
                "Hard case": row.get("hard_case"),
                "Expected": row.get("expected_label"),
                "Composite": "-" if row.get("composite") is None else row.get("composite"),
                "Band": row.get("band") or "-",
                "Verdict": row.get("status"),
            }
        )
    st.markdown("##### Hard cases")
    if hard_rows:
        st.dataframe(hard_rows, hide_index=True)
    else:
        st.caption("This run has no hard cases.")

    with st.expander("Per-scenario results"):
        rows = []
        for row in run.get("scenarios") or []:
            rows.append(
                {
                    "Scenario": row.get("scenario_id"),
                    "Category": row.get("category"),
                    "Expected": row.get("expected_label"),
                    "Composite": "-" if row.get("composite") is None else row.get("composite"),
                    "Band": row.get("band") or "-",
                    "Verdict": row.get("status"),
                    "Distance": "-" if row.get("distance") is None else row.get("distance"),
                }
            )
        st.dataframe(rows, hide_index=True)

    errors = [row for row in run.get("scenarios") or [] if row.get("status") == "error"]
    if errors:
        with st.expander("Scenario errors (%d)" % len(errors)):
            for row in errors:
                st.error("%s: %s" % (row.get("scenario_id"), row.get("error")))


def render_selftest_page():
    st.subheader("Self-test")
    st.caption(
        "The battery runs every generated scenario through the full pipeline and "
        "compares the band with the known answer. A scam counts as caught at High "
        "risk, a genuine call as passed at Low risk."
    )

    try:
        from selftest import harness  # deferred: installs retry wrappers on import
        scenario_count = len(harness.load_scenarios())
    except Exception as exc:
        harness = None
        scenario_count = 0
        st.error("The scenario list could not be read: " + readable_error(exc))

    if harness is not None:
        st.caption(
            "This battery runs %d scenarios. Each uncached scenario makes about 2 "
            "Gnani API calls; audio already cached costs none." % scenario_count
        )

    if harness is not None and st.button("Run the self-test battery", type="primary"):
        with st.spinner("Running the self-test battery. This can take a minute..."):
            try:
                run = harness.run_battery()
            except Exception as exc:
                st.error("The battery could not run: " + readable_error(exc))
            else:
                st.session_state["selftest_run"] = run
                st.session_state.pop("scorecard_pdf", None)

    run = st.session_state.get("selftest_run")
    if not run:
        st.info("Run the battery to see the scorecard.")
        return

    st.divider()
    st.markdown(
        "#### Scorecard  \nrun `%s`, threshold %.2f, scenarios %s"
        % (run.get("run_id"), float(run.get("threshold", config.THRESHOLD)), run.get("scenario_count"))
    )
    _scorecard_tables(run)

    st.divider()
    pdf = st.session_state.get("scorecard_pdf")
    if st.button("Prepare scorecard PDF"):
        try:
            from selftest import scorecard

            path = scorecard.export_pdf(run)
            with open(path, "rb") as handle:
                data = handle.read()
            st.session_state["scorecard_pdf"] = {
                "run_id": run.get("run_id"),
                "name": os.path.basename(path),
                "data": data,
            }
            pdf = st.session_state["scorecard_pdf"]
        except Exception as exc:
            st.error("The scorecard PDF could not be written: " + readable_error(exc))

    pdf = st.session_state.get("scorecard_pdf")
    if pdf and pdf.get("run_id") == run.get("run_id"):
        st.download_button(
            "Download scorecard PDF",
            data=pdf["data"],
            file_name=pdf["name"],
            mime="application/pdf",
            key="scorecard_download",
        )
    elif pdf:
        st.caption("The run changed. Prepare the PDF again for this run.")


# ---------------------------------------------------------------------------
# Section 5: incident log
# ---------------------------------------------------------------------------

def load_incidents():
    try:
        with open(config.INCIDENTS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return []
    if isinstance(data, dict):
        data = data.get("records") or []
    if not isinstance(data, list):
        raise ValueError("incident log does not contain a list")
    return [row for row in data if isinstance(row, dict)]


def incident_rows(entries):
    rows = []
    for entry in entries:
        claim = entry.get("claim") or {}
        if claim.get("detected_phrase"):
            claimed = "%s: \"%s\"" % (
                claim.get("role") or "claim",
                claim.get("detected_phrase"),
            )
        else:
            claimed = claim.get("note") or "no claim detected"

        layer1 = entry.get("layer1") or {}
        cosine = layer1.get("best_cosine")
        l2_risk = score_mod.layer2_risk((entry.get("layer2") or {}).get("hits") or [])

        rows.append(
            {
                "When": show_time(entry.get("checked_at") or entry.get("created_at")),
                "Claimed identity": short(claimed, 70),
                "Layer scores": "%s / %.2f" % (ordinal_percent(cosine), l2_risk),
                "Score": "%s / 100" % entry.get("composite", "-"),
                "Band": band_label(entry.get("band")),
                "Verdict": short(entry.get("verdict_sentence") or "-", 120),
                "Transcript excerpt": short(entry.get("transcript") or "", 160),
            }
        )
    return rows


def render_incident_page():
    st.subheader("Incident log")
    st.caption(
        "Every completed check is listed here for reference. The log stays when you "
        "restart the app, but no audio is stored in it."
    )

    try:
        entries = load_incidents()
    except Exception as exc:
        st.error("The incident log could not be read: " + readable_error(exc))
        return

    if not entries:
        st.info("No checks recorded yet. Run a check and it appears here.")
        return

    entries = sorted(
        entries,
        key=lambda entry: str(entry.get("checked_at") or entry.get("created_at") or ""),
        reverse=True,
    )

    dates = sorted(
        {
            parsed.date()
            for parsed in (
                parse_time(entry.get("checked_at") or entry.get("created_at"))
                for entry in entries
            )
            if parsed is not None
        }
    )

    if dates:
        first_day, last_day = dates[0], dates[-1]
        picked = st.date_input(
            "Date range filter",
            value=(first_day, last_day),
            min_value=first_day,
            max_value=last_day,
        )
        start = end = None
        if isinstance(picked, (tuple, list)):
            if len(picked) == 2:
                start, end = picked
            elif len(picked) == 1:
                start = end = picked[0]
        elif picked:
            start = end = picked

        if start and end:
            filtered = []
            for entry in entries:
                parsed = parse_time(entry.get("checked_at") or entry.get("created_at"))
                if parsed is not None and start <= parsed.date() <= end:
                    filtered.append(entry)
            entries = filtered

    st.caption("%d check(s) in this range." % len(entries))
    if entries:
        st.dataframe(incident_rows(entries), hide_index=True)
    else:
        st.info("No checks in this date range.")

    with st.expander("Verdict sentences"):
        for entry in entries:
            st.markdown(
                "- %s: %s"
                % (show_time(entry.get("checked_at")), entry.get("verdict_sentence") or "-")
            )


# ---------------------------------------------------------------------------
# Design system CSS v2 — Matrix/opencode theme (injected before any st.* calls)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@300;400;500;600;700&family=Martian+Mono:wght@400;500&display=swap');

:root {
  /* Color — monochrome + matrix green only */
  --bg-page: #000000;
  --bg-card: #0a0a0a;
  --text-primary: #ffffff;
  --text-secondary: #e5e5e5;
  --text-muted: #9ca3af;
  --text-dim: #6b7280;
  --accent-green: #2eff6a;
  --accent-green-dim: #1cc24b;
  --accent-green-hi: #62ff94;
  --hairline: rgba(255,255,255,0.12);

  /* Typography */
  --font-display: 'Chakra Petch', system-ui, -apple-system, Segoe UI, sans-serif;
  --font-body: 'Chakra Petch', system-ui, -apple-system, Segoe UI, sans-serif;
  --font-mono: 'Martian Mono', ui-monospace, SFMono-Regular, Menlo, monospace;

  --fs-display: clamp(2.5rem, 8vw, 6.5rem);
  --fs-h1: clamp(1.75rem, 4.5vw, 3.25rem);
  --fs-h2: clamp(1.25rem, 3vw, 2.25rem);
  --fs-body: 1rem;
  --fs-caption: 0.875rem;
  --fs-small: 0.875rem;

  --fw-light: 700;   /* display headings — ensured 700 */
  --fw-regular: 500;   /* body — 500 minimum */
  --fw-medium: 600;   /* emphasis / labels / captions */
  --fw-semibold: 700;   /* active nav, strong */

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 48px;
  --space-6: 80px;
  --space-7: 120px;

  /* Radius & borders — minimal, editorial prefers square/hairline */
  --radius-sm: 4px;
  --radius-none: 0;
  --border-w: 1px;
  --border-color: var(--hairline);
}

.stApp { font-weight: 500; }

/* ============================================================
}

/* ============================================================
   FONT HAMMER — Chakra Petch on ALL text, Martian Mono on numbers/code only
   ============================================================ */
.stApp,
.stApp *:not(pre):not(code):not(.stCodeBlock *):not([data-testid="stMetricValue"]):not([data-testid="stMetricDelta"]):not(.stDataFrame td):not(.stTable td):not(.data-readout):not(button):not([role="button"]):not(.stExpander summary):not(.stFileUploader):not([data-testid="stIconMaterial"]) {
  font-family: var(--font-body) !important;
}



/* Re-assert Chakra Petch on previously excluded layout-critical elements
   (excluded from the hammer so their internal Streamlit positioning isn't broken,
   but font must still end up Chakra Petch) */
.stApp button { font-family: var(--font-body) !important; }
.stApp [role="button"] { font-family: var(--font-body) !important; }
.stApp .stExpander summary { font-family: var(--font-body) !important; }
.stApp .stFileUploader { font-family: var(--font-body) !important; }

/* Re-assert Martian Mono on numeric/code targets (AFTER hammer so it wins at equal specificity) */
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"],
.stMetric label + div,
.stDataFrame td,
.stTable td,
.data-readout,
pre code,
.stCodeBlock,
:not(pre) > code {
  font-family: var(--font-mono) !important;
  font-variant-numeric: tabular-nums !important;
}

/* ============================================================
   PAGE BACKGROUND — dot grid (signature motif)
   ============================================================ */
.stApp {
  background-color: var(--bg-page);
  background-image: radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px);
  background-size: 20px 20px;
  background-attachment: fixed;
  color: var(--text-secondary);
  font-size: var(--fs-body);
  font-weight: var(--fw-regular);
  line-height: 1.6;
}

/* Sidebar — same dot grid */
section[data-testid="stSidebar"] {
  background-color: var(--bg-card);
  background-image: radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px);
  background-size: 20px 20px;
  background-attachment: fixed;
  border-right: var(--border-w) solid var(--border-color);
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stText,
section[data-testid="stSidebar"] label {
  color: var(--text-secondary) !important;
}

/* Hide sidebar title — main content has the only title */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] .stTitle {
  display: none;
}

/* Compact sidebar vertical rhythm — no scroll at ~700px viewport */
section[data-testid="stSidebar"] {
  padding-top: var(--space-2) !important;
  padding-bottom: var(--space-2) !important;
  padding-left: var(--space-3) !important;
  padding-right: var(--space-3) !important;
}
section[data-testid="stSidebar"] .stCaption {
  margin-top: var(--space-1) !important;
  margin-bottom: var(--space-1) !important;
  line-height: 1.3 !important;
}
section[data-testid="stSidebar"] hr,
section[data-testid="stSidebar"] .stDivider {
  margin: var(--space-2) 0 !important;
}

/* ============================================================
   DISPLAY HEADINGS — giant thin uppercase (Chakra Petch 300)
   ============================================================ */
h1, h2, h3, h4, h5, h6,
.stTitle, .stHeader, .stSubheader {
  font-family: var(--font-display) !important;
  font-weight: var(--fw-light) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  line-height: 1 !important;
  color: var(--text-primary) !important;
  margin-top: 0 !important;
  margin-bottom: var(--space-3) !important;
}
h1, .stTitle { font-size: var(--fs-display) !important; }
h2, .stHeader { font-size: var(--fs-h1) !important; }
h3, .stSubheader { font-size: var(--fs-h2) !important; }
h4 { font-size: var(--fs-h2) !important; }
h5, h6 { font-size: var(--fs-h1) !important; }

/* ============================================================
   CAPTION / SMALL TEXT — tiny muted (12-14px, #9ca3af)
   ============================================================ */
.stCaption,
.stMarkdown small,
[data-testid="stCaptionContainer"],
.caption-block {
  font-family: var(--font-body) !important;
  font-size: var(--fs-caption) !important;
  line-height: 1.25 !important;
  color: var(--text-muted) !important;
  max-width: 250px;
}
.caption-block--sm { font-size: var(--fs-small) !important; max-width: 180px; }

/* ============================================================
   META / SMALL CAPS — lowercase, tracked, muted
   ============================================================ */
.meta-line,
.small-caps {
  font-family: var(--font-body) !important;
  font-size: var(--fs-small) !important;
  font-weight: var(--fw-medium) !important;
  text-transform: lowercase !important;
  letter-spacing: 0.08em !important;
  color: var(--text-muted) !important;
}

/* ============================================================
   DATA READOUTS — Martian Mono, tabular nums, large
   ============================================================ */
[data-testid="stMetricValue"] {
  font-size: var(--fs-h1) !important;
  font-weight: var(--fw-medium) !important;
  color: var(--text-primary) !important;
  line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--font-body) !important;
  font-size: var(--fs-caption) !important;
  font-weight: var(--fw-medium) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: var(--text-muted) !important;
}
.data-readout--sm { font-size: var(--fs-h2) !important; }
.data-readout__label {
  font-family: var(--font-body) !important;
  font-size: var(--fs-caption) !important;
  font-weight: var(--fw-medium) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  color: var(--text-muted) !important;
  margin-top: var(--space-1) !important;
}

/* ============================================================
   HAIRLINE SEPARATORS
   ============================================================ */
hr, .stDivider, .hairline {
  border: 0 !important;
  height: 1px !important;
  background: var(--hairline) !important;
  margin: var(--space-4) 0 !important;
}
.hairline--short { width: 60px; margin-left: 0; }

/* ============================================================
   NAV BUTTONS (sidebar) — full width, primary for active
   ============================================================ */
section[data-testid="stSidebar"] .stButton > button {
  display: block !important;
  width: 100% !important;
  text-align: left !important;
  justify-content: flex-start !important;
  padding: 0.4rem 0.75rem !important;
  border-radius: var(--radius-sm) !important;
  font-size: var(--fs-small) !important;
  font-weight: var(--fw-medium) !important;
  font-family: var(--font-body) !important;
  border: var(--border-w) solid transparent !important;
  transition: opacity 0.2s ease, background-color 0.2s ease, border-color 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: #ffffff !important;
  color: #000000 !important;
  border-color: #ffffff !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
  background: #e5e5e5 !important;
  color: #000000 !important;
  opacity: 0.9 !important;
}
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]) {
  background: transparent !important;
  border-color: transparent !important;
  color: var(--text-secondary) !important;
}
section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):hover {
  background: rgba(255,255,255,0.05) !important;
  border-color: var(--text-dim) !important;
}
section[data-testid="stSidebar"] .stButton > button:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 2px var(--bg-page), 0 0 0 4px var(--accent-green) !important;
}

/* ============================================================
   BUTTONS (main) — minimal radius, matrix green for primary
   ============================================================ */
.stButton > button,
.stDownloadButton > button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--fs-small);
  font-weight: var(--fw-semibold);
  font-family: var(--font-body);
  border: var(--border-w) solid transparent;
  cursor: pointer;
  transition: opacity 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}
.stButton > button[kind="primary"],
.stDownloadButton > button[kind="primary"] {
  background: #ffffff !important;
  color: #000000 !important;
  border-color: #ffffff !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button[kind="primary"]:hover {
  background: #e5e5e5 !important;
  color: #000000 !important;
}
.stButton > button[kind="secondary"],
.stButton > button:not([kind="primary"]),
.stDownloadButton > button:not([kind="primary"]) {
  background: transparent !important;
  color: #ffffff !important;
  border: 1.5px solid #6b7280 !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button:not([kind="primary"]):hover,
.stDownloadButton > button:not([kind="primary"]):hover {
  background: rgba(255,255,255,0.05) !important;
  border-color: #ffffff !important;
}
.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--bg-page), 0 0 0 4px var(--accent-green);
}

/* Disabled buttons */
.stButton > button:disabled,
.stDownloadButton > button:disabled {
  color: #6b7280 !important;
  border-color: #6b7280 !important;
  background: transparent !important;
}

/* ============================================================
   FORM INPUTS — hairline borders, no radius on cards
   ============================================================ */
.stTextInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"],
.stFileUploader,
.stDateInput input,
.stNumberInput input {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
  font-size: var(--fs-body) !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stSelectbox [data-baseweb="select"]:focus,
.stFileUploader:focus-within,
.stDateInput input:focus,
.stNumberInput input:focus {
  border-color: var(--accent-green) !important;
  box-shadow: 0 0 0 2px rgba(46,255,106,0.3) !important;
}
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stFileUploader label,
.stDateInput label,
.stNumberInput label,
.stRadio label,
.stCheckbox label {
  color: var(--text-secondary) !important;
  font-size: var(--fs-small) !important;
  font-weight: var(--fw-medium) !important;
  font-family: var(--font-body) !important;
}

/* File uploader — card style, no large radius */
.stFileUploader {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  padding: var(--space-3) var(--space-4) !important;
}
.stFileUploader:hover {
  border-color: var(--text-dim) !important;
}

/* ============================================================
   DATAFRAMES / TABLES — clean, hairline borders, mono numbers
   ============================================================ */
.stDataFrame,
.stTable {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  overflow: hidden;
}
.stDataFrame [data-testid="stDataFrameContainer"],
.stTable [data-testid="stTableContainer"] {
  background: var(--bg-card) !important;
}
.stDataFrame th,
.stTable th {
  background: var(--bg-page) !important;
  color: var(--text-primary) !important;
  font-weight: var(--fw-semibold) !important;
  font-size: var(--fs-caption) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  border-bottom: var(--border-w) solid var(--hairline) !important;
  font-family: var(--font-body) !important;
  padding: var(--space-2) var(--space-3) !important;
}
.stDataFrame td,
.stTable td {
  color: var(--text-secondary) !important;
  font-size: var(--fs-small) !important;
  border-bottom: var(--border-w) solid var(--hairline) !important;
  font-family: var(--font-body) !important;
  padding: var(--space-2) var(--space-3) !important;
}
.stDataFrame td:first-child,
.stTable td:first-child {
  font-family: var(--font-mono) !important;
  font-variant-numeric: tabular-nums !important;
}
.stDataFrame tr:hover td,
.stTable tr:hover td {
  background: rgba(255,255,255,0.02) !important;
}

/* ============================================================
   EXPANDERS — square, hairline
   ============================================================ */
.stExpander {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  overflow: hidden;
}
.stExpander summary {
  background: var(--bg-page) !important;
  color: var(--text-primary) !important;
  font-weight: var(--fw-semibold) !important;
  font-family: var(--font-body) !important;
  font-size: var(--fs-body) !important;
  padding: var(--space-3) var(--space-4) !important;
  border-bottom: var(--border-w) solid var(--hairline) !important;
}
.stExpander summary:hover {
  background: rgba(255,255,255,0.02) !important;
}
.stExpanderContent {
  padding: var(--space-4) var(--space-5) !important;
  color: var(--text-secondary) !important;
}

/* ============================================================
   ALERTS — OVERRIDE ALL STREAMLIT DEFAULTS TO PALETTE
   ============================================================ */
/* Modern data-testid selectors */
[data-testid="stAlert"] {
  border-radius: var(--radius-none) !important;
  border: var(--border-w) solid var(--hairline) !important;
  padding: var(--space-3) var(--space-4) !important;
  background: var(--bg-card) !important;
  color: var(--text-secondary) !important;
}
[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] p,
[data-testid="stAlert"] svg {
  color: var(--text-secondary) !important;
  fill: var(--text-secondary) !important;
}

/* Legacy class selectors */
.stAlert,
.stInfo,
.stSuccess,
.stWarning,
.stError {
  border-radius: var(--radius-none) !important;
  border: var(--border-w) solid var(--hairline) !important;
  padding: var(--space-3) var(--space-4) !important;
  background: var(--bg-card) !important;
  color: var(--text-secondary) !important;
}

/* Info → grayscale */
.stInfo,
[data-testid="stAlert"][kind="info"] {
  border-left: 3px solid var(--text-muted) !important;
  background: var(--bg-card) !important;
}
.stInfo [data-testid="stMarkdownContainer"],
.stInfo p,
.stInfo svg {
  color: var(--text-secondary) !important;
  fill: var(--text-secondary) !important;
}

/* Success → matrix green */
.stSuccess,
[data-testid="stAlert"][kind="success"] {
  border-left: 3px solid var(--accent-green) !important;
  background: rgba(46,255,106,0.10) !important;
}
.stSuccess [data-testid="stMarkdownContainer"],
.stSuccess p,
.stSuccess svg {
  color: var(--accent-green) !important;
  fill: var(--accent-green) !important;
}

/* Warning → grayscale (NO amber/orange) */
.stWarning,
[data-testid="stAlert"][kind="warning"] {
  border-left: 3px solid var(--text-dim) !important;
  background: var(--bg-card) !important;
}
.stWarning [data-testid="stMarkdownContainer"],
.stWarning p,
.stWarning svg {
  color: var(--text-secondary) !important;
  fill: var(--text-secondary) !important;
}

/* Error → grayscale (NO red) */
.stError,
[data-testid="stAlert"][kind="error"] {
  border-left: 3px solid var(--text-primary) !important;
  background: #050505 !important;
}
.stError [data-testid="stMarkdownContainer"],
.stError p,
.stError svg {
  color: var(--text-primary) !important;
  fill: var(--text-primary) !important;
  font-weight: var(--fw-semibold) !important;
}

/* Exception */
[data-testid="stException"] {
  background: #050505 !important;
  border: var(--border-w) solid var(--text-dim) !important;
  color: var(--text-secondary) !important;
}
[data-testid="stException"] code,
[data-testid="stException"] pre {
  background: var(--bg-card) !important;
  color: var(--text-secondary) !important;
}

/* ============================================================
   TABS — clean underline, matrix green for active
   ============================================================ */
.stTabs [data-baseweb="tab-list"] {
  gap: var(--space-4) !important;
  background: transparent !important;
  border-bottom: var(--border-w) solid var(--hairline) !important;
  padding: var(--space-2) 0 !important;
  border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  font-size: var(--fs-small) !important;
  font-weight: var(--fw-medium) !important;
  font-family: var(--font-body) !important;
  padding: var(--space-1) var(--space-2) !important;
  border-radius: 0 !important;
  transition: opacity 0.2s ease, color 0.2s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
  opacity: 0.6 !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text-primary) !important;
  background: transparent !important;
}
.stTabs [aria-selected="true"]::after {
  background: var(--accent-green) !important;
  height: 2px !important;
}

/* ============================================================
   SPINNER — matrix green
   ============================================================ */
.stSpinner > div {
  border-top-color: var(--accent-green) !important;
}

/* ============================================================
   CODE BLOCKS — mono only, no terminal box
   ============================================================ */
pre code, .stCodeBlock {
  font-family: var(--font-mono) !important;
  font-size: var(--fs-small) !important;
  line-height: 1.6 !important;
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  padding: var(--space-4) !important;
  color: var(--text-secondary) !important;
  overflow-x: auto !important;
  display: block !important;
}
:not(pre) > code {
  font-family: var(--font-mono) !important;
  font-size: 0.9em !important;
  background: rgba(255,255,255,0.08) !important;
  color: var(--text-secondary) !important;
  padding: 0.15em 0.4em !important;
  border-radius: var(--radius-sm) !important;
}

/* ============================================================
   METRIC CARDS — square, hairline, no glow
   ============================================================ */
[data-testid="stMetric"] {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  padding: var(--space-4) var(--space-5) !important;
  min-height: 160px !important;
  transition: border-color 0.2s ease !important;
}
[data-testid="stMetric"]:hover {
  border-color: var(--text-dim) !important;
}

/* ============================================================
   CHECKBOX & RADIO ACCENTS — matrix green
   ============================================================ */
.stCheckbox input[type="checkbox"]:checked,
.stRadio input[type="radio"]:checked {
  accent-color: var(--accent-green) !important;
}

/* ============================================================
   LINKS IN MARKDOWN — matrix green
   ============================================================ */
.stMarkdown a {
  color: var(--accent-green) !important;
  text-decoration: none !important;
}
.stMarkdown a:hover {
  text-decoration: underline !important;
  color: var(--accent-green-hi) !important;
}

/* ============================================================
   FOCUS RINGS — matrix green
   ============================================================ */
*:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 2px var(--bg-page), 0 0 0 4px var(--accent-green) !important;
}

/* ============================================================
   ST.AUDIO CONTAINER BORDER
   ============================================================ */
.stAudio {
  border: var(--border-w) solid var(--hairline) !important;
  border-radius: var(--radius-none) !important;
  background: var(--bg-card) !important;
  padding: var(--space-2) !important;
}

/* ============================================================
   TOOLTIPS — matrix green accent
   ============================================================ */
[data-testid="stTooltip"] {
  background: var(--bg-card) !important;
  border: var(--border-w) solid var(--hairline) !important;
  color: var(--text-secondary) !important;
}
[data-testid="stTooltip"]::before {
  border-bottom-color: var(--accent-green) !important;
}

/* ============================================================
   PROGRESS BAR — matrix green
   ============================================================ */
.stProgress > div > div {
  background: var(--accent-green) !important;
}

/* ============================================================
   REDUCED MOTION — disable all transitions/animations
   ============================================================ */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ============================================================
   RESPONSIVE — clamp() handles display sizing; minor tweaks
   ============================================================ */
@media (max-width: 639px) {
  .stApp { padding: var(--space-3) var(--space-4) !important; }
  [data-testid="stMetric"] { min-height: 140px !important; }
}
@media (min-width: 640px) and (max-width: 1023px) {
  .stApp { padding: var(--space-4) var(--space-5) !important; }
}
@media (min-width: 1024px) {
  .stApp { padding: var(--space-5) var(--space-6) !important; }
}
@media (min-width: 1440px) {
  .stApp { padding: var(--space-6) var(--space-7) !important; }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="CloneGuard", page_icon="🛡️", layout="wide")

    page = sidebar()

    st.title("CloneGuard")
    st.caption(
        "Checks whether a caller's voice matches a trusted enrolled person, and "
        "scans the conversation for Hinglish scam patterns."
    )

    if not api_key_present():
        st.warning(
            "Set the environment variable GNANI_API_KEY and restart the app. "
            "Checks on cached audio still run; a new file will fail when it "
            "calls the API."
        )

    if page == "Check a call":
        render_check_page()
    elif page == "Spoken verdict":
        render_spoken_page()
    elif page == "Enroll a voice":
        render_enroll_page()
    elif page == "Self-test":
        render_selftest_page()
    elif page == "Incident log":
        render_incident_page()

    render_footer()


if __name__ == "__main__":
    main()