import os
import requests

BASE = "https://api.vachana.ai"
KEY = os.environ.get("GNANI_API_KEY")


def _check():
    if not KEY:
        raise RuntimeError("GNANI_API_KEY not found. Restart VS Code terminal.")


def text_to_speech(text, voice="Nalini", language="hi-IN", out="reply.wav"):
    """Your text -> Timbre speaks it -> saves reply.wav"""
    _check()
    r = requests.post(
        f"{BASE}/api/v1/tts/inference",
        headers={"X-API-Key-ID": KEY, "Content-Type": "application/json"},
        json={
            "text": text,
            "voice": voice,
            "model": "timbre-v2.5",
            "language": language,
            "audio_config": {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav",
            },
        },
        timeout=60,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Timbre error {r.status_code}: {r.text[:300]}")
    with open(out, "wb") as f:
        f.write(r.content)
    return out


def speech_to_text(audio_path, language_code="indic-auto"):
    """Audio file -> Prisma converts it to text"""
    _check()
    with open(audio_path, "rb") as f:
        r = requests.post(
            f"{BASE}/stt/v3",
            headers={"X-API-Key-ID": KEY},
            files={"audio_file": (os.path.basename(audio_path), f, "audio/wav")},
            data={"model": "prisma-v3.0", "language_code": language_code},
            timeout=60,
        )
    if r.status_code != 200:
        raise RuntimeError(f"Prisma error {r.status_code}: {r.text[:300]}")
    return r.json()["transcript"]