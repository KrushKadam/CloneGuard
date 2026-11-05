"""Render the latest self-test run as a scorecard dict and a one-page PDF.

    python selftest\\scorecard.py

The PDF is a calibration report, not a benchmark: every script was written by
the same person who wrote the engine, so the honesty line is printed on the
page itself.

Devanagari handling: no Devanagari-capable TTF was found on this machine
(DejaVuSans does not cover Devanagari either), so the PDF uses the built-in
core font and replaces any Devanagari run with its Latin equivalent / matched
phrase before drawing. This is stated on the PDF footer as well.
"""

import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config  # noqa: E402

RUNS_PATH = os.path.join(config.DATA_DIR, "selftest_runs.json")
PDF_DIR = os.path.join(HERE, "scorecard_pdfs")
HONESTY_LINE = "Calibration against builder-written scripts, not independent accuracy."

_DEVANAGARI = re.compile("[\u0900-\u097F]+(?:[ \t]+[\u0900-\u097F]+)*")
_PUNCT_MAP = {
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
}

DEVANAGARI_NOTE = (
    "Devanagari: no Devanagari-capable font is installed here, so the built-in "
    "core font is used and Devanagari text is replaced with its Latin equivalent "
    "(matched phrase where one exists). Nothing is dropped silently."
)


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def load_runs(path=None):
    path = path or RUNS_PATH
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("runs") or []
    if not isinstance(data, list) or not data:
        raise RuntimeError("no self-test runs found in %s" % path)
    return data


def latest_run(path=None):
    return load_runs(path)[-1]


def render(run=None):
    """Latest (or given) run as a flat scorecard dict."""
    run = latest_run() if run is None else run
    metrics = run.get("metrics") or {}
    scenarios = []
    for row in run.get("scenarios") or []:
        scenarios.append(
            {
                "scenario_id": row.get("scenario_id"),
                "category": row.get("category"),
                "expected_label": row.get("expected_label"),
                "composite": row.get("composite"),
                "band": row.get("band"),
                "status": row.get("status"),
                "distance": row.get("distance"),
                "hard_case": row.get("hard_case"),
            }
        )
    return {
        "run_id": run.get("run_id"),
        "date": run.get("started_at"),
        "scenario_count": run.get("scenario_count", len(scenarios)),
        "threshold": run.get("threshold", config.THRESHOLD),
        "scam_caught": metrics.get("scam_caught"),
        "genuine_passed": metrics.get("genuine_passed"),
        "caution_count": metrics.get("caution_count"),
        "errors": metrics.get("errors"),
        "weakest": metrics.get("weakest"),
        "scenarios": scenarios,
        "hard_cases": [row for row in scenarios if row.get("hard_case")],
        "sweep": run.get("sweep") or [],
        "honesty_line": run.get("honesty_line") or HONESTY_LINE,
    }


# ---------------------------------------------------------------------------
# PDF text safety
# ---------------------------------------------------------------------------

def latinize(text, matched_phrase=None):
    """Make text safe for the core PDF font, replacing Devanagari runs."""
    if text is None:
        return ""
    value = str(text)
    value = _DEVANAGARI.sub("" if matched_phrase is None else str(matched_phrase), value)
    for source, target in _PUNCT_MAP.items():
        value = value.replace(source, target)
    return value.encode("latin-1", "replace").decode("latin-1")


def _clip(text, width):
    text = latinize(text)
    if len(text) <= width:
        return text
    return text[: max(0, width - 3)] + "..."


# ---------------------------------------------------------------------------
# PDF backend
# ---------------------------------------------------------------------------

def _ensure_pdf_library():
    """reportlab first, fpdf/fpdf2 second, pip install fpdf2 as the last resort."""
    try:
        import reportlab  # noqa: F401

        return "reportlab"
    except ImportError:
        pass
    try:
        import fpdf  # noqa: F401

        return "fpdf"
    except ImportError:
        pass

    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--quiet", "fpdf2"]
    )
    return "fpdf"


def _write_with_fpdf(scorecard, path):
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_margins(12, 12, 12)

    # Title block
    pdf.set_font("Helvetica", "B", 17)
    pdf.cell(0, 9, latinize("CloneGuard Self-Test Scorecard"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(
        0,
        5,
        _clip("run %s   threshold %.2f   scenarios %s"
              % (scorecard["run_id"], float(scorecard["threshold"]), scorecard["scenario_count"]), 110),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(0, 5, _clip("date %s" % scorecard["date"], 110), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Headline metrics
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Headline", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    headline = [
        ("scam caught", str(scorecard["scam_caught"])),
        ("genuine passed", str(scorecard["genuine_passed"])),
        ("caution count", str(scorecard["caution_count"])),
        ("errors", str(scorecard["errors"])),
        ("weakest scenario", str(scorecard["weakest"])),
    ]
    for label, value in headline:
        pdf.cell(42, 6, latinize(label), border=0)
        pdf.cell(0, 6, _clip(value, 120), border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Hard cases
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Hard cases", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    if scorecard["hard_cases"]:
        for row in scorecard["hard_cases"]:
            pdf.cell(
                0,
                5,
                _clip("%s  [%s]  expected %s  composite %s  band %s  -> %s"
                      % (
                          row["scenario_id"],
                          row["hard_case"],
                          row["expected_label"],
                          "-" if row["composite"] is None else row["composite"],
                          row["band"] or "-",
                          row["status"],
                      ), 150),
                new_x="LMARGIN",
                new_y="NEXT",
            )
    else:
        pdf.cell(0, 5, "none", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # Per-scenario table
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Per-scenario results", new_x="LMARGIN", new_y="NEXT")
    widths = (10, 44, 18, 14, 18, 20, 16, 42)
    headers = ("#", "scenario", "expected", "comp", "band", "verdict", "dist", "case")
    pdf.set_font("Helvetica", "B", 8)
    for width, header in zip(widths, headers):
        pdf.cell(width, 5, header, border=1)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 7.5)
    for index, row in enumerate(scorecard["scenarios"], start=1):
        cells = (
            str(index),
            _clip(row["scenario_id"], 30),
            row["expected_label"],
            "-" if row["composite"] is None else str(row["composite"]),
            row["band"] or "-",
            row["status"],
            "-" if row["distance"] is None else str(row["distance"]),
            _clip(row["hard_case"] or "", 26),
        )
        for width, value in zip(widths, cells):
            pdf.cell(width, 4.6, latinize(value), border=1)
        pdf.ln(4.6)
    pdf.ln(2)

    # Threshold sweep
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Threshold sweep (stored Layer 2 risk, recomputed Layer 1)", new_x="LMARGIN", new_y="NEXT")
    sweep_widths = (28, 34, 34, 28, 28)
    pdf.set_font("Helvetica", "B", 8)
    for width, header in zip(sweep_widths, ("threshold", "scam caught", "genuine passed", "caution", "errors")):
        pdf.cell(width, 5, header, border=1)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 8)
    for row in scorecard["sweep"]:
        cells = (
            "%.2f" % float(row["threshold"]),
            str(row["scam_caught"]),
            str(row["genuine_passed"]),
            str(row["caution_count"]),
            str(row["errors"]),
        )
        for width, value in zip(sweep_widths, cells):
            pdf.cell(width, 4.6, latinize(value), border=1)
        pdf.ln(4.6)

    # Footer
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(
        0, 5, _clip(scorecard["honesty_line"], 200), new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "", 7)
    pdf.multi_cell(0, 4, DEVANAGARI_NOTE, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)
    return path


def _write_with_reportlab(scorecard, path):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    width, height = A4
    pdf = canvas.Canvas(path, pagesize=A4)
    y = height - 18 * mm
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(12 * mm, y, latinize("CloneGuard Self-Test Scorecard"))
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)
    pdf.drawString(
        12 * mm,
        y,
        _clip("run %s   threshold %.2f   scenarios %s"
              % (scorecard["run_id"], float(scorecard["threshold"]), scorecard["scenario_count"]), 100),
    )
    y -= 5 * mm
    pdf.drawString(12 * mm, y, _clip("date %s" % scorecard["date"], 100))
    y -= 8 * mm

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(12 * mm, y, "Headline")
    y -= 6 * mm
    pdf.setFont("Helvetica", 9)
    for label, value in (
        ("scam caught", scorecard["scam_caught"]),
        ("genuine passed", scorecard["genuine_passed"]),
        ("caution count", scorecard["caution_count"]),
        ("errors", scorecard["errors"]),
        ("weakest scenario", scorecard["weakest"]),
    ):
        pdf.drawString(12 * mm, y, _clip("%s: %s" % (label, value), 110))
        y -= 5 * mm

    y -= 3 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(12 * mm, y, "Per-scenario results")
    y -= 6 * mm
    pdf.setFont("Helvetica", 7.5)
    for index, row in enumerate(scorecard["scenarios"], start=1):
        pdf.drawString(
            12 * mm,
            y,
            latinize(
                "%2d  %-30s %-8s comp %-4s %-7s %-7s dist %-3s %s"
                % (
                    index,
                    _clip(row["scenario_id"], 30),
                    row["expected_label"],
                    "-" if row["composite"] is None else row["composite"],
                    row["band"] or "-",
                    row["status"],
                    "-" if row["distance"] is None else row["distance"],
                    _clip(row["hard_case"] or "", 20),
                )
            ),
        )
        y -= 4.2 * mm

    y -= 3 * mm
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(12 * mm, y, "Threshold sweep")
    y -= 6 * mm
    pdf.setFont("Helvetica", 8)
    for row in scorecard["sweep"]:
        pdf.drawString(
            12 * mm,
            y,
            "threshold %.2f   scam %s   genuine %s   caution %s   errors %s"
            % (
                float(row["threshold"]),
                row["scam_caught"],
                row["genuine_passed"],
                row["caution_count"],
                row["errors"],
            ),
        )
        y -= 4.2 * mm

    y -= 4 * mm
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(12 * mm, y, _clip(scorecard["honesty_line"], 100))
    y -= 5 * mm
    pdf.setFont("Helvetica", 7)
    pdf.drawString(12 * mm, y, _clip(DEVANAGARI_NOTE, 150))
    pdf.showPage()
    pdf.save()
    return path


def export_pdf(run=None, path=None):
    """Write the scorecard PDF and return its absolute path."""
    scorecard = render(run)
    os.makedirs(PDF_DIR, exist_ok=True)
    if path is None:
        stamp = re.sub(r"[^0-9A-Za-z]+", "_", str(scorecard["run_id"] or "run"))
        path = os.path.join(PDF_DIR, "scorecard_%s.pdf" % stamp)
    backend = _ensure_pdf_library()
    if backend == "reportlab":
        _write_with_reportlab(scorecard, path)
    else:
        _write_with_fpdf(scorecard, path)
    return os.path.abspath(path)


def main():
    scorecard = render()
    path = export_pdf()
    print("run_id      %s" % scorecard["run_id"])
    print("scam caught %s   genuine passed %s   caution %s   errors %s"
          % (scorecard["scam_caught"], scorecard["genuine_passed"],
             scorecard["caution_count"], scorecard["errors"]))
    print("weakest     %s" % scorecard["weakest"])
    print("pdf         %s (%d bytes)" % (path, os.path.getsize(path)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
