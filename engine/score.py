"""Scoring: Layer 1 + Layer 2 -> 0-100 composite and a band.

Formulas (fixed):
    layer1_risk = clamp((threshold - best_cosine) / threshold, 0, 1)
    layer2_risk = min(1, sum(hit weights) / LAYER2_DIVISOR)
    composite   = round(100 * (W_L1 * layer1_risk + W_L2 * layer2_risk))
    bands       = 0-29 low, 30-59 caution, 60-100 high

When there is no comparable voiceprint the Layer 2 risk alone is rescaled to
0-100. Layer 1 only ever reports an identity match or an identity mismatch.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

BAND_SENTENCES = {
    "low": (
        "The caller's voice is consistent with the enrolled person and no scam "
        "patterns matched. This is a weak signal, not a clearance."
    ),
    "caution": (
        "One layer raised a concern. Ask a verification question the real "
        "person would answer."
    ),
    "high": (
        "The caller does not match the claimed person's voice, or the "
        "conversation uses known scam patterns, or both. Treat this call as unsafe."
    ),
}


def clamp(value, low=0.0, high=1.0):
    if value < low:
        return low
    if value > high:
        return high
    return value


def layer1_risk(best_cosine, threshold=None):
    threshold = config.THRESHOLD if threshold is None else threshold
    if best_cosine is None:
        return None
    return clamp((threshold - best_cosine) / threshold, 0.0, 1.0)


def layer2_risk(hits, divisor=None):
    divisor = config.LAYER2_DIVISOR if divisor is None else divisor
    total = sum(float(hit.get("weight") or 0.0) for hit in hits or [])
    return min(1.0, total / divisor)


def band_for(composite):
    low_cut, high_cut = config.BAND_CUTOFFS
    if composite < low_cut:
        return "low"
    if composite < high_cut:
        return "caution"
    return "high"


def score_case(best_cosine, hits, comparable=True):
    """Combine both layers. `comparable` is False when no voiceprint applies."""
    l2 = layer2_risk(hits)
    if comparable and best_cosine is not None:
        l1 = layer1_risk(best_cosine)
        composite = round(100 * (config.W_L1 * l1 + config.W_L2 * l2))
    else:
        l1 = None
        composite = round(100 * l2)
    band = band_for(composite)
    return {
        "layer1_risk": None if l1 is None else round(l1, 4),
        "layer2_risk": round(l2, 4),
        "composite": composite,
        "band": band,
        "verdict_sentence": BAND_SENTENCES[band],
        "layer1_scored": l1 is not None,
    }
