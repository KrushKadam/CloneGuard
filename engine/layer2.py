"""Layer 2: known scam-phrase scan over a transcript.

Matching is substring based on a normalized transcript: lowercase, punctuation
removed, whitespace collapsed. Devanagari combining marks are preserved, so the
same phrase list works whether Prisma returns Latin or Devanagari script.

scan() always returns a list. Zero hits is a valid, meaningful result.
"""

import json
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

_ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"


def normalize_text(text):
    """Lowercase, strip punctuation, collapse whitespace."""
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", str(text)).lower()
    kept = []
    for char in value:
        if char in _ZERO_WIDTH:
            continue
        if unicodedata.category(char).startswith("P"):
            kept.append(" ")
        else:
            kept.append(char)
    return " ".join("".join(kept).split())


def load_patterns(path=None):
    path = path or config.PATTERNS_PATH
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("patterns") or []
    return [row for row in data if isinstance(row, dict)]


def _snippet(original, normalized, position, length):
    """About 80 characters of the original text either side of the match."""
    text_len = len(original)
    index_len = max(1, len(normalized))
    centre = int(position / index_len * text_len)
    width = max(1, int(length / index_len * text_len))
    start = max(0, centre - 80)
    end = min(text_len, centre + width + 80)
    body = original[start:end].strip()
    if start > 0:
        body = "..." + body
    if end < text_len:
        body = body + "..."
    return body


def scan(transcript, patterns):
    """Return one hit per matched pattern id (never a boolean)."""
    original = transcript or ""
    index = normalize_text(original)
    hits = []
    if not index or not patterns:
        return hits

    for record in patterns:
        variants = record.get("phrase_variants") or []
        matched_phrase = None
        position = -1
        matched_len = 0
        for variant in variants:
            cleaned = normalize_text(variant)
            if not cleaned:
                continue
            found = index.find(cleaned)
            if found != -1:
                matched_phrase = variant
                position = found
                matched_len = len(cleaned)
                break
        if matched_phrase is None:
            continue

        hits.append(
            {
                "id": record.get("id"),
                "category": record.get("category"),
                "matched_phrase": matched_phrase,
                "transcript_snippet": _snippet(
                    original, index, position, matched_len
                ),
                "severity": record.get("severity"),
                "weight": float(record.get("weight") or 0.0),
            }
        )
    return hits
