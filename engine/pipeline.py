"""The CloneGuard check: audio file in, scored result dict out.

Flow:
    validate file -> speech_to_text -> Layer 2 scan -> embedding (cached)
    -> resolve claimed identity -> Layer 1 compare -> composite + band

A missing/empty file is rejected before any API credit is spent.
"""

import datetime
import json
import os
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
import gnani

try:
    from . import claim as claim_mod
    from . import layer1
    from . import layer2
    from . import score
except ImportError:  # running from inside engine\ as plain scripts
    import claim as claim_mod
    import layer1
    import layer2
    import score


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _cache_key(audio_path):
    path = os.path.abspath(audio_path)
    stat = os.stat(path)
    return "%s|%d|%d" % (path.lower(), stat.st_size, int(stat.st_mtime))


def _load_stt_cache():
    try:
        with open(config.STT_CACHE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_stt_cache(cache):
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        temp_path = config.STT_CACHE_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, config.STT_CACHE_PATH)
    except OSError:
        pass


def transcribe(audio_path):
    """Prisma transcript, reused for the same unchanged file."""
    key = _cache_key(audio_path)
    cache = _load_stt_cache()
    if key in cache:
        return cache[key]
    text = gnani.speech_to_text(
        os.path.abspath(audio_path), language_code=config.LANGUAGE_CODE
    )
    cache[key] = text
    _save_stt_cache(cache)
    return text


def _validate(audio_path):
    if not isinstance(audio_path, (str, os.PathLike)):
        raise TypeError("audio_path must be a path, got %r" % type(audio_path))
    path = os.path.abspath(os.fspath(audio_path))
    if not os.path.exists(path):
        raise FileNotFoundError("audio file not found: %s" % path)
    if os.path.isdir(path):
        raise ValueError("audio_path is a directory: %s" % path)
    if os.path.getsize(path) <= 0:
        raise ValueError("audio file is empty: %s" % path)
    return path


def run_check(audio_path, save=False):
    """Score one call recording. Returns the result dict described in README."""
    path = _validate(audio_path)
    notes = []

    transcript = transcribe(path)
    patterns = layer2.load_patterns(config.PATTERNS_PATH)
    hits = layer2.scan(transcript, patterns)

    voiceprints = layer1.load_voiceprints()
    claim = claim_mod.resolve_claim(transcript, voiceprints)
    default = layer1.get_default(voiceprints)
    target_id = claim.get("voiceprint_id") or (default.get("id") if default else None)
    comparable = bool(target_id) and bool(claim.get("enrolled"))

    embedding = layer1.get_embedding_cached(path)
    comparisons = layer1.compare(embedding, voiceprints, target_id=target_id)
    target_row = next((row for row in comparisons if row.get("target")), None)
    best_cosine = target_row.get("cosine") if target_row else None

    if comparable and best_cosine is not None:
        label = (
            "identity match"
            if target_row.get("verdict") == "match"
            else "identity mismatch"
        )
    else:
        label = "not scored (no enrolled voiceprint for the claim)"
        best_cosine = None

    scores = score.score_case(
        best_cosine, hits, comparable=comparable and best_cosine is not None
    )

    if claim.get("note"):
        notes.append(claim["note"])
    if not voiceprints:
        notes.append("no voiceprints enrolled — Layer 1 was not scored")
    elif claim.get("detected_phrase") and not claim.get("enrolled"):
        notes.append(
            "Layer 1 was not scored: the claim names someone who is not enrolled"
        )
    elif not claim.get("detected_phrase") and default:
        notes.append(
            "Layer 1 compared against the default voiceprint (%s)"
            % (default.get("role") or default.get("name") or default.get("id"))
        )
    if not scores["layer1_scored"]:
        notes.append("composite comes from Layer 2 alone, rescaled to 0-100")

    result = {
        "audio_path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
        "transcript": transcript,
        "layer1": {
            "comparisons": comparisons,
            "target_id": target_id,
            "best_cosine": best_cosine,
            "threshold": config.THRESHOLD,
            "label": label,
            "comparable": comparable,
        },
        "claim": claim,
        "layer2": {"hits": hits},
        "composite": scores["composite"],
        "band": scores["band"],
        "verdict_sentence": scores["verdict_sentence"],
        "notes": notes,
        "checked_at": _now(),
    }

    if save:
        save_record(result)
    return result


def _load_incidents():
    try:
        with open(config.INCIDENTS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def save_record(record):
    """Append one check result to data\\incidents.json."""
    os.makedirs(config.DATA_DIR, exist_ok=True)
    rows = _load_incidents()
    entry = dict(record)
    entry.setdefault("id", "inc_" + uuid.uuid4().hex[:12])
    entry.setdefault("created_at", _now())
    rows.append(entry)
    temp_path = config.INCIDENTS_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, config.INCIDENTS_PATH)
    return entry
