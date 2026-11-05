"""Generate CloneGuard test calls: Hinglish script -> Gnani Timbre TTS -> WAV.

Every call is written to samples\\ after a light telephone-band post-process,
and a record is appended to data\\scenarios.json (existing records are kept).

Run from the project root:

    python generator\\generate.py
"""

import argparse
import array
import datetime
import json
import math
import os
import random
import sys
import tempfile
import wave

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (ROOT, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import gnani  # noqa: E402  (project root module; imported after sys.path setup)
import scripts  # noqa: E402  (generator/scripts.py)

SAMPLE_RATE = 48000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM

SCAM_VOICE = "Deepak"
GENUINE_VOICE = "Nalini"
LANGUAGE = "hi-IN"

SAMPLES_DIR = os.path.join(ROOT, "samples")
DATA_DIR = os.path.join(ROOT, "data")
SCENARIOS_PATH = os.path.join(DATA_DIR, "scenarios.json")

# Telephone band: keep speech intelligible, just remove the studio polish.
HIGHPASS_HZ = 320.0
LOWPASS_HZ = 3400.0
NOISE_AMPLITUDE = 40  # int16 counts, roughly -58 dBFS of line hiss
FADE_MS = 8


# ---------------------------------------------------------------------------
# WAV helpers (stdlib only: wave + array/struct)
# ---------------------------------------------------------------------------

def _read_wav(path):
    """Return (samples, sample_rate, channels) as 16-bit ints."""
    with wave.open(path, "rb") as reader:
        channels = reader.getnchannels()
        width = reader.getsampwidth()
        rate = reader.getframerate()
        frames = reader.readframes(reader.getnframes())

    if width != 2:
        raise RuntimeError("expected 16-bit PCM, got %d-bit" % (width * 8))

    samples = array.array("h")
    samples.frombytes(frames)
    if sys.byteorder == "big":
        samples.byteswap()
    return samples, rate, channels


def _to_mono(samples, channels):
    if channels == 1:
        return samples
    mono = array.array("h")
    append = mono.append
    for start in range(0, len(samples), channels):
        chunk = samples[start:start + channels]
        append(int(sum(chunk) / len(chunk)))
    return mono


def _resample(samples, src_rate, dst_rate):
    if src_rate == dst_rate or not samples:
        return samples
    ratio = dst_rate / float(src_rate)
    out_len = max(1, int(round(len(samples) * ratio)))
    out = array.array("h", [0]) * out_len
    last = len(samples) - 1
    for i in range(out_len):
        pos = i / ratio
        i0 = int(pos)
        if i0 >= last:
            out[i] = samples[last]
            continue
        frac = pos - i0
        out[i] = int(samples[i0] * (1.0 - frac) + samples[i0 + 1] * frac)
    return out


def _clamp16(value):
    if value > 32767:
        return 32767
    if value < -32768:
        return -32768
    return int(value)


def _lowpass(samples, cutoff, rate):
    alpha = 1.0 - math.exp(-2.0 * math.pi * cutoff / rate)
    out = array.array("h")
    append = out.append
    y = float(samples[0]) if samples else 0.0
    for value in samples:
        y += alpha * (value - y)
        append(_clamp16(y))
    return out


def _highpass(samples, cutoff, rate):
    alpha = 1.0 - math.exp(-2.0 * math.pi * cutoff / rate)
    out = array.array("h")
    append = out.append
    y = float(samples[0]) if samples else 0.0
    for value in samples:
        y += alpha * (value - y)
        append(_clamp16(value - y))
    return out


def _apply_fade(samples, rate, ms=FADE_MS):
    n = min(len(samples) // 2, int(rate * ms / 1000.0))
    for i in range(n):
        gain = i / float(n)
        samples[i] = int(samples[i] * gain)
        samples[-1 - i] = int(samples[-1 - i] * gain)


def _write_wav(path, samples, rate):
    payload = array.array("h", samples)
    if sys.byteorder == "big":
        payload.byteswap()
    with wave.open(path, "wb") as writer:
        writer.setnchannels(CHANNELS)
        writer.setsampwidth(SAMPLE_WIDTH)
        writer.setframerate(rate)
        writer.writeframes(payload.tobytes())


def apply_phone_effect(src_path, dst_path, seed=20261105):
    """Band-limit + low-level noise, written as 48 kHz mono 16-bit WAV."""
    samples, rate, channels = _read_wav(src_path)
    samples = _to_mono(samples, channels)
    samples = _resample(samples, rate, SAMPLE_RATE)
    samples = _highpass(samples, HIGHPASS_HZ, SAMPLE_RATE)
    samples = _lowpass(samples, LOWPASS_HZ, SAMPLE_RATE)
    samples = _lowpass(samples, LOWPASS_HZ, SAMPLE_RATE)  # steeper roll-off

    rng = random.Random(seed)
    for i in range(len(samples)):
        samples[i] = max(-32768, min(32767, samples[i] + rng.randint(-NOISE_AMPLITUDE, NOISE_AMPLITUDE)))

    peak = 0
    for value in samples:
        if value > peak:
            peak = value
        elif -value > peak:
            peak = -value
    if peak > 32000:
        scale = 32000.0 / peak
        for i in range(len(samples)):
            samples[i] = int(samples[i] * scale)

    _apply_fade(samples, SAMPLE_RATE)
    _write_wav(dst_path, samples, SAMPLE_RATE)
    return dst_path


# ---------------------------------------------------------------------------
# Scenario records
# ---------------------------------------------------------------------------

def _load_scenarios(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "cannot read existing %s (%s); move or fix it, refusing to overwrite"
            % (path, exc)
        )
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("scenarios"), list):
        return data["scenarios"]
    raise RuntimeError(
        "%s does not contain a list of scenarios; refusing to overwrite" % path
    )


def _save_scenarios(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, path)


def _unique_path(directory, stem):
    candidate = os.path.join(directory, stem + ".wav")
    counter = 2
    while os.path.exists(candidate):
        candidate = os.path.join(directory, "%s_v%d.wav" % (stem, counter))
        counter += 1
    return candidate


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def build_jobs(scam_voice=SCAM_VOICE, genuine_voice=GENUINE_VOICE):
    jobs = []
    for family in scripts.SCAM_ORDER:
        category, text = scripts.get_scam_script(family)
        jobs.append(
            {
                "category": category,
                "type": "scam",
                "expected_label": "scam",
                "script_text": text,
                "voice": scam_voice,
            }
        )
    for index in range(len(scripts.GENUINE_ORDER)):
        category, text = scripts.get_genuine_script(index)
        jobs.append(
            {
                "category": category,
                "type": "genuine",
                "expected_label": "genuine",
                "script_text": text,
                "voice": genuine_voice,
            }
        )
    return jobs


def run_job(job, stamp, call_counter):
    """Generate one call. Returns a record dict, or None on failure."""
    stem = "gc_%s_%s_%s" % (job["type"], job["category"], stamp)
    final_path = _unique_path(SAMPLES_DIR, stem)

    with tempfile.NamedTemporaryFile(
        prefix="_raw_", suffix=".wav", dir=DATA_DIR, delete=False
    ) as handle:
        raw_path = handle.name

    try:
        last_error = None
        for attempt in (1, 2):
            try:
                call_counter[0] += 1
                gnani.text_to_speech(
                    job["script_text"],
                    voice=job["voice"],
                    language=LANGUAGE,
                    out=raw_path,
                )
                last_error = None
                break
            except Exception as exc:  # API/network failure: retry once, then give up
                last_error = exc
                if attempt == 1:
                    print("  retrying once after: %s" % exc)
        if last_error is not None:
            raise last_error

        apply_phone_effect(raw_path, final_path)
        if not os.path.exists(final_path) or os.path.getsize(final_path) <= 1000:
            raise RuntimeError("post-processed WAV is missing or smaller than 1001 bytes")

        record = {
            "category": job["category"],
            "type": job["type"],
            "script_text": job["script_text"],
            "timbre_voice": job["voice"],
            "audio_path": os.path.relpath(final_path, ROOT).replace(os.sep, "/"),
            "expected_label": job["expected_label"],
            "created_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        return record
    finally:
        try:
            os.remove(raw_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate CloneGuard scam-call test WAVs.")
    parser.add_argument("--scam-voice", default=SCAM_VOICE, help="Timbre voice for scam calls")
    parser.add_argument("--genuine-voice", default=GENUINE_VOICE, help="Timbre voice for genuine calls")
    args = parser.parse_args(argv)

    os.makedirs(SAMPLES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        records = _load_scenarios(SCENARIOS_PATH)
    except RuntimeError as exc:
        print("ERROR:", exc)
        return 1

    jobs = build_jobs(args.scam_voice, args.genuine_voice)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    call_counter = [0]
    results = []

    for index, job in enumerate(jobs, start=1):
        print("[%d/%d] %s (%s, voice=%s)" % (index, len(jobs), job["category"], job["type"], job["voice"]))
        try:
            record = run_job(job, stamp, call_counter)
            if record is None:
                raise RuntimeError("no record produced")
            records.append(record)
            _save_scenarios(SCENARIOS_PATH, records)
            results.append((os.path.basename(record["audio_path"]), job["voice"], job["expected_label"]))
            print("  OK -> %s" % record["audio_path"])
        except Exception as exc:
            results.append((None, job["voice"], job["expected_label"]))
            print("  ERROR [%s]: %s" % (job["category"], exc))

    successes = sum(1 for row in results if row[0])
    print()
    print("%-50s %-8s %-8s" % ("filename", "voice", "label"))
    print("-" * 68)
    for filename, voice, label in results:
        print("%-50s %-8s %-8s" % (filename or "<failed>", voice, label))
    print()
    print("TTS calls: %d (max 2 per scenario)" % call_counter[0])
    if successes == len(jobs):
        print("GENERATOR_OK (%d/%d)" % (successes, len(jobs)))
    else:
        print("GENERATOR_PARTIAL (%d/%d)" % (successes, len(jobs)))
    return 0 if successes == len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
