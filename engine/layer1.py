"""Layer 1: voiceprint enrollment and speaker comparison.

A voiceprint record is a JSON-friendly dict:

    {"id", "name", "role", "embedding": [768 floats], "source_path", "created_at"}

Embeddings come from Gnani's voice-clone endpoint via voiceprint.get_embedding().
An audio file is embedded at most once per process and once per unchanged file
on disk, so a single check spends one embedding credit at most.
"""

import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config
import voiceprint as vp

_MEMORY_CACHE = {}
_DISK_CACHE = None


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _slug(value):
    text = re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")
    return text or "voiceprint"


def _cache_key(audio_path):
    path = os.path.abspath(audio_path)
    stat = os.stat(path)
    return "%s|%d|%d" % (path.lower(), stat.st_size, int(stat.st_mtime))


def _load_disk_cache():
    global _DISK_CACHE
    if _DISK_CACHE is not None:
        return _DISK_CACHE
    _DISK_CACHE = {}
    try:
        with open(config.EMBEDDING_CACHE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            _DISK_CACHE = data
    except (OSError, ValueError):
        _DISK_CACHE = {}
    return _DISK_CACHE


def _save_disk_cache(cache):
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        temp_path = config.EMBEDDING_CACHE_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(cache, handle, ensure_ascii=False)
            handle.write("\n")
        os.replace(temp_path, config.EMBEDDING_CACHE_PATH)
    except OSError:
        pass


def get_embedding_cached(audio_path):
    """Embedding for this audio file, reused for the same unchanged file."""
    key = _cache_key(audio_path)
    if key in _MEMORY_CACHE:
        return _MEMORY_CACHE[key]
    cache = _load_disk_cache()
    vector = cache.get(key)
    if not isinstance(vector, list) or not vector:
        vector = vp.get_embedding(os.path.abspath(audio_path))
        cache[key] = vector
        _save_disk_cache(cache)
    _MEMORY_CACHE[key] = vector
    return vector


def load_voiceprints():
    """All enrolled voiceprints, or [] when nothing is enrolled yet."""
    try:
        with open(config.VOICEPRINTS_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):
        data = data.get("voiceprints") or []
    return [row for row in data if isinstance(row, dict)]


def save_voiceprints(records):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    temp_path = config.VOICEPRINTS_PATH + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, config.VOICEPRINTS_PATH)
    return records


def _new_id(seed, records):
    base = "vp_" + _slug(seed)
    taken = {row.get("id") for row in records}
    if base not in taken:
        return base
    counter = 2
    while "%s_%d" % (base, counter) in taken:
        counter += 1
    return "%s_%d" % (base, counter)


def enroll(wav_path, name, role):
    """Enroll (or re-enroll) one speaker. Same role replaces the same id."""
    if not os.path.isfile(wav_path):
        raise FileNotFoundError(wav_path)
    if os.path.getsize(wav_path) <= 0:
        raise ValueError("audio file is empty: %s" % wav_path)

    embedding = get_embedding_cached(wav_path)
    records = load_voiceprints()

    role_key = (role or "").strip().lower()
    existing = None
    for row in records:
        if role_key and (row.get("role") or "").strip().lower() == role_key:
            existing = row
            break

    record = {
        "id": existing["id"] if existing else _new_id(role or name, records),
        "name": name,
        "role": role,
        "embedding": [round(float(value), 6) for value in embedding],
        "source_path": os.path.relpath(os.path.abspath(wav_path), ROOT).replace(os.sep, "/"),
        "created_at": _now(),
    }

    if existing is None:
        records.append(record)
    else:
        records[records.index(existing)] = record
    save_voiceprints(records)
    _MEMORY_CACHE[_cache_key(wav_path)] = embedding
    return record


def get_default(voiceprints=None):
    """First enrolled record, unless config pins a default id."""
    rows = load_voiceprints() if voiceprints is None else voiceprints
    if not rows:
        return None
    wanted = config.DEFAULT_VOICEPRINT_ID
    if wanted:
        for row in rows:
            if row.get("id") == wanted:
                return row
    return rows[0]


def compare(embedding, voiceprints, target_id=None):
    """Cosine of `embedding` against every voiceprint.

    Returns one row per voiceprint with the target row flagged. When no target
    id is given, the closest voiceprint is treated as the target.
    """
    rows = []
    for row in voiceprints or []:
        vector = row.get("embedding") or []
        try:
            similarity = round(float(vp.cosine(embedding, vector)), 4)
        except (ValueError, TypeError, ZeroDivisionError):
            rows.append(
                {
                    "voiceprint_id": row.get("id"),
                    "name": row.get("name"),
                    "role": row.get("role"),
                    "cosine": None,
                    "threshold": config.THRESHOLD,
                    "verdict": "dimension mismatch",
                    "target": row.get("id") == target_id,
                }
            )
            continue
        rows.append(
            {
                "voiceprint_id": row.get("id"),
                "name": row.get("name"),
                "role": row.get("role"),
                "cosine": similarity,
                "threshold": config.THRESHOLD,
                "verdict": "match" if similarity >= config.THRESHOLD else "mismatch",
                "target": row.get("id") == target_id,
            }
        )

    if target_id is None and rows:
        scored = [row for row in rows if row["cosine"] is not None]
        if scored:
            max(scored, key=lambda row: row["cosine"])["target"] = True
    return rows
