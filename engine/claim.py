"""Identity claim resolution: who does the caller say they are?

Lookup only, no fuzzy matching. Works on the same normalized text as Layer 2,
with Latin and Devanagari variants.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

try:
    from . import layer2
except ImportError:  # running from inside engine\ as plain scripts
    import layer2

CLAIMS = [
    (
        "Papa",
        [
            "main papa bol raha hoon",
            "papa bol raha hoon",
            "papa here",
            "beta main hoon",
            "main tumhara papa",
            "मैं पापा बोल रहा हूँ",
            "पापा बोल रहा हूँ",
            "पापा हियर",
            "बेटा मैं हूँ",
            "मैं तुम्हारा पापा",
            "मैं पापा हूँ",
        ],
    ),
    (
        "Mummy",
        [
            "main mummy bol raha hoon",
            "main mummy bol rahi hoon",
            "mummy bol rahi hoon",
            "मैं मम्मी बोल रहा हूँ",
            "मैं मम्मी बोल रही हूँ",
            "मम्मी बोल रही हूँ",
            "मैं मम्मी हूँ",
        ],
    ),
    (
        "CEO",
        [
            "main ceo bol raha hoon",
            "ceo bol raha hoon",
            "main ceo",
            "boss bol raha hoon",
            "मैं सीईओ बोल रहा हूँ",
            "सीईओ बोल रहा हूँ",
            "मैं सीईओ",
            "बॉस बोल रहा हूँ",
        ],
    ),
]


def _default(voiceprints):
    rows = voiceprints or []
    if not rows:
        return None
    wanted = config.DEFAULT_VOICEPRINT_ID
    if wanted:
        for row in rows:
            if row.get("id") == wanted:
                return row
    return rows[0]


def _find_voiceprint(voiceprints, role):
    role_key = role.strip().lower()
    for row in voiceprints or []:
        if (row.get("role") or "").strip().lower() == role_key:
            return row
    return None


def resolve_claim(transcript, voiceprints):
    """Resolve the identity the caller claims, and the voiceprint to compare.

    Returns {detected_phrase, role, voiceprint_id, enrolled, note}.
    """
    index = layer2.normalize_text(transcript)

    detected_phrase = None
    claimed_role = None
    if index:
        for role, variants in CLAIMS:
            for variant in variants:
                cleaned = layer2.normalize_text(variant)
                if cleaned and cleaned in index:
                    detected_phrase = variant
                    claimed_role = role
                    break
            if detected_phrase:
                break

    if detected_phrase is None:
        fallback = _default(voiceprints)
        return {
            "detected_phrase": None,
            "role": None,
            "voiceprint_id": fallback.get("id") if fallback else None,
            "enrolled": bool(fallback),
            "note": "no claim detected — comparing against the default voiceprint",
        }

    match = _find_voiceprint(voiceprints, claimed_role)
    if match:
        return {
            "detected_phrase": detected_phrase,
            "role": claimed_role,
            "voiceprint_id": match.get("id"),
            "enrolled": True,
            "note": "claim detected: caller says they are %s" % claimed_role,
        }

    fallback = _default(voiceprints)
    return {
        "detected_phrase": detected_phrase,
        "role": claimed_role,
        "voiceprint_id": fallback.get("id") if fallback else None,
        "enrolled": False,
        "note": "claim names someone not enrolled",
    }
