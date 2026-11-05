"""Step 2 self-test: enroll one voice, score one scam call and one genuine call.

Run from the project root:

    python engine\\test_step2.py

Prints STEP2_OK only when both expectations hold.
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for path in (ROOT, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

import config
import layer1
import pipeline

SCAM = os.path.join(config.SAMPLES_DIR, "gc_scam_bank_fraud_20261105_093045.wav")
GENUINE = os.path.join(config.SAMPLES_DIR, "gc_genuine_friend_dinner_20261105_093045.wav")
ENROLL = os.path.join(config.SAMPLES_DIR, "A1_nalini_X.wav")


def show(title, result):
    layer1_row = result["layer1"]
    hits = result["layer2"]["hits"]
    print("")
    print("== %s ==" % title)
    print("file: %s" % result["audio_path"])
    print("transcript[:100]: %s" % result["transcript"][:100].replace("\n", " "))
    print(
        "layer1: target=%s cosine=%s label=%s"
        % (layer1_row["target_id"], layer1_row["best_cosine"], layer1_row["label"])
    )
    print("claim: %s" % result["claim"]["note"])
    print("layer2 hits: %d" % len(hits))
    for hit in hits:
        print(
            "  - [%s/%s] %s (w=%s)"
            % (hit["category"], hit["severity"], hit["matched_phrase"], hit["weight"])
        )
    for row in layer1_row["comparisons"]:
        print("  compare %s (%s): cosine=%s %s" % (row["name"], row["voiceprint_id"], row["cosine"], row["verdict"]))
    print("composite: %s  band: %s" % (result["composite"], result["band"]))
    print("verdict: %s" % result["verdict_sentence"])
    if result["notes"]:
        print("notes: %s" % "; ".join(result["notes"]))


def main():
    print("enrolling %s as Nalini / Papa ..." % os.path.basename(ENROLL))
    record = layer1.enroll(ENROLL, "Nalini", "Papa")
    print(
        "enrolled: id=%s name=%s role=%s dim=%d"
        % (record["id"], record["name"], record["role"], len(record["embedding"]))
    )

    scam = pipeline.run_check(SCAM)
    genuine = pipeline.run_check(GENUINE)
    show("scam bank fraud", scam)
    show("genuine friend dinner", genuine)

    problems = []
    scam_hits = len(scam["layer2"]["hits"])
    genuine_hits = len(genuine["layer2"]["hits"])

    if scam["layer1"]["label"] != "identity mismatch":
        problems.append("scam layer1 label %r != 'identity mismatch'" % scam["layer1"]["label"])
    if scam_hits < 1:
        problems.append("scam layer2 hits %d < 1" % scam_hits)
    if scam["composite"] < 60:
        problems.append("scam composite %d < 60" % scam["composite"])
    if scam["band"] != "high":
        problems.append("scam band %r != 'high'" % scam["band"])

    if genuine["layer1"]["label"] != "identity match":
        problems.append("genuine layer1 label %r != 'identity match'" % genuine["layer1"]["label"])
    if genuine_hits != 0:
        problems.append("genuine layer2 hits %d != 0" % genuine_hits)
    if genuine["composite"] > 29:
        problems.append("genuine composite %d > 29" % genuine["composite"])
    if genuine["band"] != "low":
        problems.append("genuine band %r != 'low'" % genuine["band"])

    print("")
    if problems:
        print("STEP2_FAIL")
        for problem in problems:
            print("  mismatch: %s" % problem)
        return 1
    print(
        "STEP2_OK (scam %d/%s with %d hits, genuine %d/%s with %d hits)"
        % (
            scam["composite"],
            scam["band"],
            scam_hits,
            genuine["composite"],
            genuine["band"],
            genuine_hits,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
