import os, sys, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
KEY = os.environ.get("GNANI_API_KEY")

print("Workspace:", ROOT)
print("Python:", sys.version.split()[0])
print("Key loaded:", "YES" if KEY else "NO")
print("Docs:", sorted(os.listdir(os.path.join(ROOT, "docs"))))

# API connectivity probe: deliberately incomplete request (no audio file).
# Server answering 422 proves key + endpoint + internet work. Validation
# errors do not consume credits.
r = requests.post(
    "https://api.vachana.ai/stt/v3",
    headers={"X-API-Key-ID": KEY},
    data={"model": "prisma-v3.0", "language_code": "indic-auto"},
    timeout=30,
)
ok = r.status_code == 422 and "audio_file" in r.text
print("Gnani API:", "REACHABLE (422 expected, key accepted)" if ok else f"UNEXPECTED {r.status_code}: {r.text[:200]}")
print("STATUS:", "CONNECTED" if ok else "FAILED")