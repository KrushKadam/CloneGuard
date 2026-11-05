"""CloneGuard self-test harness: run every scenario, score the calls, keep history.

The battery is deliberately blunt:

    scam scenario    -> useful only if the band is "high"   (caught)
    genuine scenario -> useful only if the band is "low"    (passed)
    band "caution"   -> a miss in both directions, tallied separately

Nothing here changes the engine. It reads data\\scenarios.json, calls
engine.pipeline.run_check for each record, and appends one run to
data\\selftest_runs.json. API failures are caught per scenario and surface as
status "error", never as a crash.

Run from the project root:

    python selftest\\harness.py
"""

import datetime
import json
import os
import sys
import tempfile
import uuid

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config  # noqa: E402
import gnani  # noqa: E402
import voiceprint as vp  # noqa: E402
from engine import pipeline, score  # noqa: E402

SCENARIOS_PATH = os.path.join(config.DATA_DIR, "scenarios.json")
RUNS_PATH = os.path.join(config.DATA_DIR, "selftest_runs.json")

SWEEP_THRESHOLDS = (0.45, 0.50, 0.55, 0.60, 0.65)
HONESTY_LINE = "Calibration against builder-written scripts, not independent accuracy."

# API calls are counted after the retry wrapper below is installed.
API_CALLS = {"stt": 0, "embedding": 0, "tts": 0}

NO_URGENCY_CATEGORY = "bank_refund_no_urgency"
NO_URGENCY_TAG = "scam without urgency words"
NO_URGENCY_SCRIPT = (
    "Namaste ji, main bank ke refund department se baat kar raha hoon. "
    "Aapke account mein ek refund pending hai jo hum aapko wapas karna chahte hain. "
    "Aap apna account number verify kar lijiye, uske baad main aapko link khol kar "
    "details confirm karne ko kahunga. Aap apne samay se yeh kar lijiye, main yahin "
    "available hoon. Koi bhi sawaal ho to mujhe bata dijiye."
)


# ---------------------------------------------------------------------------
# API retry (at most one retry per call) + call counting
# ---------------------------------------------------------------------------

def _retry_once(func, counter_key):
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in (1, 2):
            API_CALLS[counter_key] = API_CALLS.get(counter_key, 0) + 1
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # network / API failure: one retry, then raise
                last_error = exc
                if attempt == 2:
                    raise
        raise last_error

    wrapper._cg_wrapped = True  # type: ignore[attr-defined]
    wrapper.__name__ = getattr(func, "__name__", "wrapped")
    return wrapper


def _install_retry_wrappers():
    if not getattr(gnani.speech_to_text, "_cg_wrapped", False):
        gnani.speech_to_text = _retry_once(gnani.speech_to_text, "stt")
    if not getattr(vp.get_embedding, "_cg_wrapped", False):
        vp.get_embedding = _retry_once(vp.get_embedding, "embedding")


_install_retry_wrappers()


# ---------------------------------------------------------------------------
# Scenario records
# ---------------------------------------------------------------------------

def load_scenarios():
    with open(SCENARIOS_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("scenarios") or []
    if not isinstance(data, list):
        raise RuntimeError("%s does not contain a list of scenarios" % SCENARIOS_PATH)
    return [row for row in data if isinstance(row, dict)]


def _save_scenarios(records):
    temp_path = SCENARIOS_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, SCENARIOS_PATH)


def _expected_band(expected_label):
    return "high" if expected_label == "scam" else "low"


def _distance(expected_label, composite):
    if composite is None:
        return None
    if expected_label == "scam":
        return max(0, 60 - composite)
    return max(0, composite - 29)


def _slug(value):
    text = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").lower())
    return "_".join(part for part in text.split("_") if part) or "scenario"


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _band_status(expected_label, band):
    """caught / passed / missed, with caution always a miss."""
    if expected_label == "scam":
        return "caught" if band == "high" else "missed"
    return "passed" if band == "low" else "missed"


# ---------------------------------------------------------------------------
# Threshold sweep (stored Layer 2 risk, recomputed Layer 1 risk)
# ---------------------------------------------------------------------------

def recomposite(best_cosine, hits, threshold):
    """Composite at an arbitrary Layer 1 threshold; Layer 2 risk is unchanged."""
    l2 = score.layer2_risk(hits)
    if best_cosine is None:
        return round(100 * l2)
    l1 = score.clamp((threshold - best_cosine) / threshold, 0.0, 1.0)
    return round(100 * (config.W_L1 * l1 + config.W_L2 * l2))


def sweep(scenario_rows, thresholds=SWEEP_THRESHOLDS):
    table = []
    for threshold in thresholds:
        caught = passed = caution = errors = 0
        for row in scenario_rows:
            if row["status"] == "error":
                errors += 1
                continue
            composite = recomposite(row["best_cosine"], row["hits"], threshold)
            band = score.band_for(composite)
            if band == "caution":
                caution += 1
            if row["expected_label"] == "scam" and band == "high":
                caught += 1
            elif row["expected_label"] == "genuine" and band == "low":
                passed += 1
        table.append(
            {
                "threshold": round(float(threshold), 2),
                "scam_caught": "%d/%d" % (caught, sum(1 for r in scenario_rows if r["expected_label"] == "scam" and r["status"] != "error")),
                "genuine_passed": "%d/%d" % (passed, sum(1 for r in scenario_rows if r["expected_label"] == "genuine" and r["status"] != "error")),
                "caution_count": caution,
                "errors": errors,
            }
        )
    return table


# ---------------------------------------------------------------------------
# Battery
# ---------------------------------------------------------------------------

def run_battery():
    """Run every scenario once. Returns (run_record, console_lines)."""
    started_at = _now()
    run_id = "run_%s_%s" % (
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
        uuid.uuid4().hex[:4],
    )
    scenarios = load_scenarios()
    rows = []

    for index, record in enumerate(scenarios, start=1):
        category = record.get("category") or "unknown"
        expected = record.get("expected_label") or record.get("type") or "scam"
        audio_path = os.path.join(ROOT, str(record.get("audio_path") or "").replace("/", os.sep))
        row = {
            "scenario_id": "sc%02d_%s" % (index, _slug(category)),
            "category": category,
            "expected_label": expected,
            "hard_case": record.get("hard_case"),
            "audio_path": record.get("audio_path"),
            "composite": None,
            "band": None,
            "status": "error",
            "distance": None,
            "best_cosine": None,
            "hits": [],
            "error": None,
        }
        try:
            result = pipeline.run_check(audio_path)
            row["composite"] = result.get("composite")
            row["band"] = result.get("band")
            row["best_cosine"] = (result.get("layer1") or {}).get("best_cosine")
            row["hits"] = (result.get("layer2") or {}).get("hits") or []
            row["status"] = _band_status(expected, row["band"])
            row["distance"] = _distance(expected, row["composite"])
        except Exception as exc:  # API/engine failure: record it, keep going
            row["status"] = "error"
            row["error"] = "%s: %s" % (type(exc).__name__, exc)
        rows.append(row)

    scam_rows = [r for r in rows if r["expected_label"] == "scam"]
    genuine_rows = [r for r in rows if r["expected_label"] == "genuine"]
    caught = sum(1 for r in scam_rows if r["status"] == "caught")
    passed = sum(1 for r in genuine_rows if r["status"] == "passed")
    caution_count = sum(1 for r in rows if r["band"] == "caution")
    errors = sum(1 for r in rows if r["status"] == "error")

    scored = [r for r in rows if r["distance"] is not None]
    weakest = None
    if scored:
        weakest = max(scored, key=lambda r: r["distance"])

    metrics = {
        "scam_caught": "%d/%d" % (caught, len(scam_rows)),
        "genuine_passed": "%d/%d" % (passed, len(genuine_rows)),
        "caution_count": caution_count,
        "errors": errors,
        "weakest": (
            "%s (composite %s, distance %s)"
            % (weakest["category"], weakest["composite"], weakest["distance"])
            if weakest
            else "n/a"
        ),
        "weakest_category": weakest["category"] if weakest else None,
        "weakest_composite": weakest["composite"] if weakest else None,
        "weakest_distance": weakest["distance"] if weakest else None,
    }

    run = {
        "run_id": run_id,
        "started_at": started_at,
        "threshold": config.THRESHOLD,
        "scenario_count": len(rows),
        "metrics": metrics,
        "scenarios": rows,
        "sweep": sweep(rows),
        "honesty_line": HONESTY_LINE,
    }
    return run


def _load_runs():
    if not os.path.exists(RUNS_PATH):
        return []
    try:
        with open(RUNS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            "cannot read %s (%s); fix or move it, refusing to overwrite history"
            % (RUNS_PATH, exc)
        )
    if isinstance(data, dict):
        data = data.get("runs") or []
    if not isinstance(data, list):
        raise RuntimeError("%s does not contain a list of runs" % RUNS_PATH)
    return data


def save_run(run):
    """Append-only history: existing runs are never replaced."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    runs = _load_runs()
    runs.append(run)
    temp_path = RUNS_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(runs, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, RUNS_PATH)
    return RUNS_PATH


# ---------------------------------------------------------------------------
# Optional hard case: a scam script with no urgency words at all
# ---------------------------------------------------------------------------

def add_no_urgency_scenario():
    """Generate the no-urgency scam call once and append its scenario record.

    Reuses generator.generate.apply_phone_effect for the telephone-band
    post-process instead of copying it. Idempotent: returns the existing record
    if the tag is already present.
    """
    records = load_scenarios()
    for record in records:
        if record.get("hard_case") == NO_URGENCY_TAG:
            return record

    from generator import generate as gen  # deferred: keeps plain battery runs light

    os.makedirs(config.SAMPLES_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = "gc_scam_no_urgency_%s" % stamp
    final_path = os.path.join(config.SAMPLES_DIR, stem + ".wav")
    counter = 2
    while os.path.exists(final_path):
        final_path = os.path.join(config.SAMPLES_DIR, "%s_v%d.wav" % (stem, counter))
        counter += 1

    with tempfile.NamedTemporaryFile(
        prefix="_raw_", suffix=".wav", dir=config.DATA_DIR, delete=False
    ) as handle:
        raw_path = handle.name

    try:
        API_CALLS["tts"] = API_CALLS.get("tts", 0) + 1
        try:
            gnani.text_to_speech(
                NO_URGENCY_SCRIPT, voice="Deepak", language="hi-IN", out=raw_path
            )
        except Exception:
            API_CALLS["tts"] = API_CALLS.get("tts", 0) + 1
            gnani.text_to_speech(
                NO_URGENCY_SCRIPT, voice="Deepak", language="hi-IN", out=raw_path
            )
        gen.apply_phone_effect(raw_path, final_path)
        if not os.path.exists(final_path) or os.path.getsize(final_path) <= 1000:
            raise RuntimeError("post-processed WAV is missing or too small")
    finally:
        try:
            os.remove(raw_path)
        except OSError:
            pass

    record = {
        "category": NO_URGENCY_CATEGORY,
        "type": "scam",
        "script_text": NO_URGENCY_SCRIPT,
        "timbre_voice": "Deepak",
        "audio_path": os.path.relpath(final_path, ROOT).replace(os.sep, "/"),
        "expected_label": "scam",
        "created_at": _now(),
        "hard_case": NO_URGENCY_TAG,
    }
    records.append(record)
    _save_scenarios(records)
    return record


# ---------------------------------------------------------------------------
# Console scorecard
# ---------------------------------------------------------------------------

def format_scorecard(run):
    metrics = run["metrics"]
    rows = run["scenarios"]
    lines = []
    lines.append("=" * 78)
    lines.append("CloneGuard self-test  |  %s" % run["started_at"])
    lines.append("run_id %s   threshold %.2f   scenarios %d"
                 % (run["run_id"], run["threshold"], run["scenario_count"]))
    lines.append("-" * 78)
    lines.append("%-26s %-9s %4s %-8s %-8s %s"
                 % ("scenario", "expected", "comp", "band", "verdict", "distance"))
    for row in rows:
        lines.append(
            "%-26s %-9s %4s %-8s %-8s %s%s"
            % (
                row["scenario_id"][:26],
                row["expected_label"],
                "-" if row["composite"] is None else row["composite"],
                row["band"] or "-",
                row["status"],
                "-" if row["distance"] is None else row["distance"],
                "   [%s]" % row["hard_case"] if row.get("hard_case") else "",
            )
        )
    lines.append("-" * 78)
    hard = [r for r in rows if r.get("hard_case")]
    if hard:
        lines.append("hard cases")
        for row in hard:
            lines.append(
                "  %-26s %-8s comp %-4s band %-7s %s  (%s)"
                % (
                    row["scenario_id"][:26],
                    row["expected_label"],
                    "-" if row["composite"] is None else row["composite"],
                    row["band"] or "-",
                    row["status"],
                    row["hard_case"],
                )
            )
    lines.append("scam caught     %s" % metrics["scam_caught"])
    lines.append("genuine passed  %s" % metrics["genuine_passed"])
    lines.append("caution         %d" % metrics["caution_count"])
    lines.append("errors          %d" % metrics["errors"])
    lines.append("weakest         %s" % metrics["weakest"])
    lines.append("-" * 78)
    lines.append("%-10s %-14s %-14s %-8s %s"
                 % ("threshold", "scam caught", "genuine passed", "caution", "errors"))
    for row in run["sweep"]:
        lines.append(
            "%-10.2f %-14s %-14s %-8d %d"
            % (
                row["threshold"],
                row["scam_caught"],
                row["genuine_passed"],
                row["caution_count"],
                row["errors"],
            )
        )
    lines.append("-" * 78)
    for row in rows:
        if row["status"] == "error":
            lines.append("ERROR %s: %s" % (row["scenario_id"], row["error"]))
    lines.append("api calls: stt=%d embedding=%d tts=%d"
                 % (API_CALLS.get("stt", 0), API_CALLS.get("embedding", 0), API_CALLS.get("tts", 0)))
    lines.append(HONESTY_LINE)
    if metrics["errors"] == 0:
        lines.append("HARNESS_OK")
    else:
        lines.append("HARNESS_PARTIAL (%d errors)" % metrics["errors"])
    lines.append("=" * 78)
    return lines


def main():
    run = run_battery()
    save_run(run)
    print("\n".join(format_scorecard(run)))
    return 0 if run["metrics"]["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
