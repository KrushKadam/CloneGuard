"""CloneGuard configuration: paths, thresholds, model names, score weights.

Everything tunable lives here so the engine modules stay dumb.
"""

import os

APP_VERSION = "0.1.0"

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
SAMPLES_DIR = os.path.join(ROOT, "samples")

VOICEPRINTS_PATH = os.path.join(DATA_DIR, "voiceprints.json")
PATTERNS_PATH = os.path.join(DATA_DIR, "patterns.json")
INCIDENTS_PATH = os.path.join(DATA_DIR, "incidents.json")

# Local caches: re-running a check never re-bills the same audio.
EMBEDDING_CACHE_PATH = os.path.join(DATA_DIR, "embedding_cache.json")
STT_CACHE_PATH = os.path.join(DATA_DIR, "stt_cache.json")

# Layer 1: cosine similarity needed to call two voiceprints the same speaker.
THRESHOLD = 0.55

# Speech to text.
STT_MODEL = "prisma-v3.0"
LANGUAGE_CODE = "indic-auto"

# Score weights.
W_L1 = 0.5
W_L2 = 0.5

# Sum of Layer 2 hit weights that counts as a saturated (1.0) Layer 2 risk.
LAYER2_DIVISOR = 0.8

# Composite score band cutoffs: [0, 30) low, [30, 60) caution, [60, 100] high.
BAND_CUTOFFS = (30, 60)

# Optional: pin the fallback voiceprint. None = first enrolled record.
DEFAULT_VOICEPRINT_ID = None
