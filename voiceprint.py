"""CloneGuard core: speaker embeddings ("voiceprints") from Gnani's voice-cloning API.

Public API:
    get_embedding(audio_path) -> list[float]
    cosine(a, b) -> float

The Gnani embeddings endpoint returns the vector as a *string*, so parsing is
defensive on purpose (JSON list, comma separated floats, torch/numpy repr, or a
base64 blob of little-endian float32/bfloat16).
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
import struct

import requests

BASE = "https://api.vachana.ai"

# Candidate paths, tried in order until one is not 404/405.
EMBEDDING_PATHS = [
    "/api/v1/tts/voice-clone/embeddings",
    "/api/v1/tts/voice-clone/embedding",
    "/api/v1/tts/voice-clone/embed",
    "/api/v1/voice-clone/embeddings",
    "/api/v1/tts/embeddings",
    "/api/v1/embeddings",
]

_working_path: str | None = None
_last_path_errors: list[str] = []


def get_api_key() -> str:
    """Env var first, then the Windows *User* environment (HKCU\\Environment)."""
    key = os.environ.get("GNANI_API_KEY")
    if key and key.strip():
        return key.strip()
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            value, _ = winreg.QueryValueEx(h, "GNANI_API_KEY")
            if isinstance(value, str) and value.strip():
                return value.strip()
    except Exception:
        pass
    raise RuntimeError(
        "GNANI_API_KEY not found (checked process env and HKCU\\Environment)."
    )


# --------------------------------------------------------------------------- #
# embedding parsing
# --------------------------------------------------------------------------- #

_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _flatten(obj):
    if isinstance(obj, (list, tuple)):
        out = []
        for item in obj:
            out.extend(_flatten(item))
        return out
    return [obj]


def _to_floats(seq):
    vals = []
    for item in seq:
        if isinstance(item, str):
            try:
                vals.append(float(item))
            except ValueError:
                continue
        else:
            try:
                vals.append(float(item))
            except (TypeError, ValueError):
                continue
    return vals


def _decode_blob(text: str):
    """Fallback for base64-packed vectors (float32 or bfloat16, little endian)."""
    compact = re.sub(r"\s+", "", text)
    if len(compact) < 64 or not re.fullmatch(r"[A-Za-z0-9+/=_-]+", compact):
        return None
    try:
        raw = base64.b64decode(compact + "=" * (-len(compact) % 4), validate=False)
    except Exception:
        return None
    if len(raw) % 4:
        return None
    n = len(raw) // 4
    if n < 16 or n > 8192:
        return None
    f32 = list(struct.unpack("<%df" % n, raw))
    if all(math.isfinite(v) and abs(v) < 100 for v in f32):
        return f32
    # bfloat16 = high 16 bits of float32
    bf = list(struct.unpack("<%dH" % (len(raw) // 2), raw))
    f = [struct.unpack("<f", struct.pack("<I", w << 16))[0] for w in bf]
    if all(math.isfinite(v) and abs(v) < 100 for v in f):
        return f
    return None


def parse_embedding(raw) -> list[float]:
    """Turn whatever the API gave us into a flat list of floats."""
    if raw is None:
        raise ValueError("embedding payload is None")

    if isinstance(raw, dict):
        for key in ("embedding", "embeddings", "vector", "data", "result", "output"):
            if key in raw:
                try:
                    return parse_embedding(raw[key])
                except Exception:
                    continue
        # nested wrappers, e.g. {"data": {"voice_clone_embedding": {"embedding": "..."}}}
        for value in raw.values():
            if isinstance(value, (dict, list)):
                try:
                    return parse_embedding(value)
                except Exception:
                    continue
        raise ValueError(f"no embedding field in dict keys={list(raw)[:8]}")

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")

    if isinstance(raw, (list, tuple)):
        vals = _to_floats(_flatten(raw))
        if vals:
            return vals
        raise ValueError("list payload contained no numbers")

    if not isinstance(raw, str):
        raise TypeError(f"unsupported embedding type {type(raw)!r}")

    s = raw.strip()
    if not s:
        raise ValueError("embedding string is empty")

    # 1) plain JSON
    try:
        obj = json.loads(s)
        if isinstance(obj, (list, dict)):
            return parse_embedding(obj)
    except Exception:
        pass

    # 2) torch / numpy repr: tensor([...], dtype=torch.bfloat16) / array([...])
    start, end = s.find("["), s.rfind("]")
    if start != -1 and end > start:
        body = s[start + 1 : end]
        vals = _to_floats(re.split(r"[\s,;]+", body.strip()))
        if vals:
            return vals

    # 3) bare comma / whitespace separated
    vals = _to_floats(re.split(r"[\s,;]+", s))
    if len(vals) >= 16:
        return vals

    # 4) base64 blob
    blob = _decode_blob(s)
    if blob:
        return blob

    # 5) last resort: regex scrape (avoids pulling digits out of dtype names)
    vals = _to_floats(_NUM.findall(s))
    if vals:
        return vals

    raise ValueError(f"could not parse embedding string (starts {s[:60]!r})")


# --------------------------------------------------------------------------- #
# API calls
# --------------------------------------------------------------------------- #

def _post_embedding(path: str, audio_path: str, key: str) -> requests.Response:
    with open(audio_path, "rb") as fh:
        return requests.post(
            BASE + path,
            headers={"X-API-Key-ID": key},
            files={"audio_file": (os.path.basename(audio_path), fh, "audio/wav")},
            timeout=120,
        )


def get_embedding(audio_path: str, verbose: bool = False) -> list[float]:
    """audio file -> speaker embedding (list of floats)."""
    global _working_path, _last_path_errors

    if not os.path.exists(audio_path):
        raise FileNotFoundError(audio_path)

    key = get_api_key()
    paths = [_working_path] if _working_path else list(EMBEDDING_PATHS)
    _last_path_errors = []

    for path in paths:
        r = _post_embedding(path, audio_path, key)
        if r.status_code in (404, 405):
            _last_path_errors.append(f"{path} -> {r.status_code}")
            continue
        if r.status_code == 401:
            raise RuntimeError(f"401 Unauthorized on {path}: {r.text[:300]}")
        if r.status_code != 200:
            raise RuntimeError(f"embeddings error {r.status_code} on {path}: {r.text[:400]}")

        try:
            payload = r.json()
        except Exception:
            raise RuntimeError(f"non-JSON embeddings response on {path}: {r.text[:300]}")

        vec = parse_embedding(payload)
        _working_path = path
        if verbose:
            print(f"  endpoint OK: POST {path}")
            if isinstance(payload, dict):
                print(
                    "  response keys:",
                    list(payload.keys()),
                    "| shape:",
                    payload.get("shape"),
                    "| dtype:",
                    payload.get("dtype"),
                )
            print(f"  parsed dim: {len(vec)}")
        return vec

    raise RuntimeError(
        "no embeddings endpoint matched. Tried: " + "; ".join(_last_path_errors)
    )


def cosine(a, b) -> float:
    """Cosine similarity, pure Python."""
    if len(a) != len(b):
        raise ValueError(f"dimension mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        raise ValueError("zero-norm embedding")
    return dot / (na * nb)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        v = get_embedding(sys.argv[1], verbose=True)
        print("dim:", len(v), "first 3:", v[:3])
    else:
        print("usage: python voiceprint.py <audio.wav>")
