"""CloneGuard feasibility experiment: do Gnani voiceprints separate speakers?

A1 = Voice A (Nalini) reading sentence X
A2 = Voice A (Nalini) reading sentence Y   -> same speaker, different text
B1 = Voice B (Deepak) reading sentence X   -> different speaker, same text

PASS rule (initial heuristic):
    gap = cos(A1,A2) - cos(A1,B1) >= 0.15  AND  cos(A1,A2) >= 0.6
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import wave

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gnani import text_to_speech  # noqa: E402
from voiceprint import cosine, get_embedding  # noqa: E402

SAMPLES = os.path.join(HERE, "samples")
OUT_JSON = os.path.join(SAMPLES, "embeddings.json")

VOICE_A = "Nalini"   # female
VOICE_B = "Deepak"   # male

SENTENCE_X = "Main abhi office se ghar ja raha hoon."
SENTENCE_Y = "Kal ki meeting do baje hogi."

SAMPLES_SPEC = [
    ("A1", VOICE_A, SENTENCE_X, "A1_nalini_X.wav"),
    ("A2", VOICE_A, SENTENCE_Y, "A2_nalini_Y.wav"),
    ("B1", VOICE_B, SENTENCE_X, "B1_deepak_X.wav"),
]

FORCE = "--force" in sys.argv


def wav_seconds(path: str) -> float:
    """Duration from the data chunk size; Gnani's header writes a placeholder
    frame count (2147483647), so wave.getnframes() is unusable."""
    try:
        with wave.open(path, "rb") as w:
            fr = w.getframerate() or 1
            frame_bytes = max(1, w.getnchannels() * w.getsampwidth())
            try:
                n = w.getnframes()
            except Exception:
                n = 0
            if n <= 0 or n > 10_000_000:
                n = max(0, os.path.getsize(path) - 44) // frame_bytes
            return n / float(fr)
    except Exception:
        return -1.0


def ensure_sample(name: str, voice: str, text: str, filename: str) -> str:
    path = os.path.join(SAMPLES, filename)
    if not FORCE and os.path.exists(path) and os.path.getsize(path) > 1000:
        print(f"  {name}: reusing {filename} ({os.path.getsize(path)} bytes)")
        return path
    print(f"  {name}: TTS voice={voice} text={text!r}")
    text_to_speech(text, voice=voice, language="hi-IN", out=path)
    size = os.path.getsize(path)
    print(f"      -> {filename} {size} bytes, {wav_seconds(path):.2f}s")
    if size < 1000:
        raise RuntimeError(f"TTS produced a suspiciously small file for {name}")
    return path


def main() -> int:
    os.makedirs(SAMPLES, exist_ok=True)

    print("=== STEP 1: generate samples ===")
    paths = {}
    for name, voice, text, filename in SAMPLES_SPEC:
        paths[name] = ensure_sample(name, voice, text, filename)

    print("\n=== STEP 2: extract voiceprints ===")
    embeddings = {}
    for name, _voice, _text, filename in SAMPLES_SPEC:
        print(f"  {name}: POST embeddings for {filename}")
        embeddings[name] = get_embedding(paths[name], verbose=True)

    dims = {n: len(v) for n, v in embeddings.items()}
    if len(set(dims.values())) != 1:
        raise RuntimeError(f"embedding dimensions differ: {dims}")

    print("\n=== STEP 3: cosine similarities ===")
    same_spk_diff_text = cosine(embeddings["A1"], embeddings["A2"])
    diff_spk_same_text = cosine(embeddings["A1"], embeddings["B1"])
    cross = cosine(embeddings["A2"], embeddings["B1"])
    gap = same_spk_diff_text - diff_spk_same_text

    print(f"  same speaker, different text  cos(A1, A2) = {same_spk_diff_text: .4f}   (expect HIGH)")
    print(f"  diff speaker, same text       cos(A1, B1) = {diff_spk_same_text: .4f}   (expect LOW)")
    print(f"  diff speaker, different text  cos(A2, B1) = {cross: .4f}   (informational)")
    print(f"  GAP = cos(A1,A2) - cos(A1,B1) = {gap: .4f}   (need >= 0.15)")

    ok = gap >= 0.15 and same_spk_diff_text >= 0.6
    verdict = "GAP OK" if ok else "GAP FAIL"

    record = {
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "voices": {"A": VOICE_A, "B": VOICE_B},
        "sentences": {"X": SENTENCE_X, "Y": SENTENCE_Y},
        "embedding_dim": dims["A1"],
        "samples": {
            name: {
                "voice": voice,
                "text": text,
                "file": os.path.join("samples", filename),
                "embedding": embeddings[name],
            }
            for name, voice, text, filename in SAMPLES_SPEC
        },
        "results": {
            "same_spk_diff_text_A1_A2": same_spk_diff_text,
            "diff_spk_same_text_A1_B1": diff_spk_same_text,
            "diff_spk_diff_text_A2_B1": cross,
            "gap": gap,
            "thresholds": {"min_gap": 0.15, "min_same_spk": 0.6},
            "verdict": verdict,
        },
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    print(f"\n  saved -> {OUT_JSON}")

    print("\n" + "=" * 62)
    print(f"  same_spk_diff_text : {same_spk_diff_text: .4f}")
    print(f"  diff_spk_same_text : {diff_spk_same_text: .4f}")
    print(f"  gap                : {gap: .4f}")
    print(f"  VERDICT: {verdict}")
    print("=" * 62)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
