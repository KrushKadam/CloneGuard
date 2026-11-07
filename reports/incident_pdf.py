"""Render one stored check as a PDF evidence report.

    path = render_incident_pdf(record)

The record comes from data\\incidents.json. This module never re-runs the
pipeline and never calls a Gnani endpoint, so exporting a report spends no
credits and cannot change a verdict.

Layout follows docs/04_ARCHITECTURE.md, Section 11. Styling is plain: one
accent colour, one sans-serif family, tables sized to A4.

Devanagari: Windows ships Nirmala UI inside C:\\Windows\\Fonts\\Nirmala.ttc.
When a Devanagari-capable face is found, it is extracted once to a temp cache,
embedded as a subset in the PDF, and used for the whole page so Hindi text is
readable in the report. When no such face exists, the built-in core font is
used and Devanagari runs are replaced with their Latin equivalent (the matched
phrase where one exists) and a note is printed on the page. Nothing is dropped
silently.
"""

import datetime
import glob
import logging
import os
import re
import sys
import tempfile
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config  # noqa: E402
from engine import score as score_mod  # noqa: E402
from fpdf import FPDF  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.join(HERE, "out")

ACCENT = (13, 92, 99)
INK = (33, 37, 41)
MUTED = (108, 117, 125)
RULE = (206, 212, 218)
TINT = (234, 244, 242)

BAND_LABELS = {"low": "Low risk", "caution": "Caution", "high": "High risk"}

LIMITATIONS = [
    "A perfect clone of the enrolled voice passes the voice match. Matching an "
    "identity is not proof that the audio is genuine.",
    "A mismatch is not proof of synthetic audio. It flags a difference between "
    "the caller and the enrolled voice, which catches clones and human "
    "impersonators alike.",
    "Analysis runs on Gnani's cloud and needs an internet connection. Audio "
    "leaves this machine for transcription and voiceprint extraction.",
    "\"No patterns found\" means the phrase list did not match. It does not "
    "mean the call is safe.",
]

FALLBACK_NOTE = (
    "Devanagari: no Devanagari-capable font was found on this machine, so the "
    "built-in core font is used and Devanagari text is replaced with its Latin "
    "equivalent (the matched phrase where one exists). Nothing is dropped "
    "silently."
)

_DEVANAGARI_RE = re.compile("[\u0900-\u097F]")
_DEVANAGARI_RUN = re.compile("[\u0900-\u097F]+(?:[ \t\u200d]+[\u0900-\u097F]+)*")
_PUNCT_MAP = {
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
    "\u200b": "",
}

_FONT_CACHE = {}


# ---------------------------------------------------------------------------
# Text handling
# ---------------------------------------------------------------------------

def has_devanagari(text):
    return bool(_DEVANAGARI_RE.search(str(text or "")))


def latinize(text, matched_phrase=None):
    """Core-font safe text: Devanagari runs become their Latin equivalent."""
    value = "" if text is None else str(text)
    value = _DEVANAGARI_RUN.sub(
        "" if matched_phrase is None else str(matched_phrase), value
    )
    for source, target in _PUNCT_MAP.items():
        value = value.replace(source, target)
    value = "".join(ch for ch in value if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    return value.encode("latin-1", "replace").decode("latin-1")


def _clean(text):
    value = "" if text is None else str(text)
    for source, target in _PUNCT_MAP.items():
        value = value.replace(source, target)
    return "".join(ch for ch in value if ch == "\n" or ch == "\t" or ord(ch) >= 32)


# ---------------------------------------------------------------------------
# Devanagari font discovery (cached for the process)
# ---------------------------------------------------------------------------

def _cache_font_dir():
    path = os.path.join(tempfile.gettempdir(), "cloneguard_fonts")
    os.makedirs(path, exist_ok=True)
    return path


def _face_covers_devanagari(font):
    try:
        cmap = font.getBestCmap()
    except Exception:
        return False
    return all(cp in cmap for cp in (0x0915, 0x093F, 0x094D, 0x0930))


def _collect_faces():
    """Every Devanagari-capable face under C:\\Windows\\Fonts, by family."""
    from fontTools.ttLib import TTCollection, TTFont

    pattern_dir = os.environ.get("WINDIR", r"C:\Windows") + "\\Fonts"
    names = []
    for pattern in ("Nirmala*.tt*", "Mangal*.tt*", "Kokila*.tt*"):
        names.extend(glob.glob(os.path.join(pattern_dir, pattern)))
    families = {}
    for path in sorted(set(names)):
        try:
            if path.lower().endswith(".ttc"):
                collection = TTCollection(path, lazy=False)
                faces = list(collection.fonts)
            else:
                faces = [TTFont(path, lazy=False)]
        except Exception:
            continue
        for face in faces:
            if not _face_covers_devanagari(face):
                continue
            try:
                family = face["name"].getDebugName(1) or os.path.basename(path)
                style = (face["name"].getDebugName(2) or "").lower()
            except Exception:
                continue
            families.setdefault(family, {})[style or "regular"] = (face, path)
    return families


def _extract_face(family, style, face, source_path):
    digest = "%s-%s-%s" % (
        re.sub(r"[^0-9A-Za-z]+", "_", family),
        re.sub(r"[^0-9A-Za-z]+", "_", style),
        int(os.path.getmtime(source_path)),
    )
    target = os.path.join(_cache_font_dir(), digest + ".ttf")
    if not os.path.exists(target):
        face.save(target)
    return target


def devanagari_font():
    """{'name', 'regular', 'bold'} for a usable face, or None."""
    if "face" in _FONT_CACHE:
        return _FONT_CACHE["face"]
    result = None
    try:
        # The MERG table in Nirmala cannot be subset; the warning is harmless.
        logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
        families = _collect_faces()
        ordered = sorted(
            families.items(),
            key=lambda item: (
                0 if item[0].lower() == "nirmala ui"
                else 1 if "nirmala" in item[0].lower()
                else 2,
                item[0],
            ),
        )
        for family, styles in ordered:
            regular = styles.get("regular") or next(iter(styles.values()), None)
            if regular is None:
                continue
            bold = styles.get("bold")
            regular_path = _extract_face(family, "regular", regular[0], regular[1])
            bold_path = (
                _extract_face(family, "bold", bold[0], bold[1])
                if bold is not None
                else regular_path
            )
            result = {"name": family, "regular": regular_path, "bold": bold_path}
            break
    except Exception:
        result = None
    _FONT_CACHE["face"] = result
    return result


# ---------------------------------------------------------------------------
# Small record readers
# ---------------------------------------------------------------------------

def _text(value, matched_phrase=None):
    face = devanagari_font()
    value = _clean(value)
    if face is None:
        return latinize(value, matched_phrase)
    return value


def _absolute(audio_path):
    value = str(audio_path or "")
    if not value:
        return ""
    if os.path.isabs(value):
        return value
    return os.path.normpath(os.path.join(ROOT, value.replace("/", os.sep)))


def audio_facts(record):
    path = _absolute(record.get("audio_path"))
    name = os.path.basename(path) or "not stored"
    duration = "not available"
    rate = "not available"
    try:
        with wave.open(path, "rb") as reader:
            frames = reader.getnframes()
            rate_value = reader.getframerate()
            if rate_value:
                seconds = frames / float(rate_value)
                duration = ("%d min %02d s" % divmod(round(seconds), 60)
                            if seconds >= 60 else "%.1f s" % seconds)
                rate = "%d Hz" % rate_value
    except Exception:
        pass

    lowered = path.replace("\\", "/").lower()
    generated = "/samples/" in lowered or name.lower().startswith("gc_")
    source = "generated with Timbre" if generated else "uploaded by the user"
    return {"name": name, "duration": duration, "rate": rate, "source": source}


def _timestamp(record):
    return str(record.get("checked_at") or record.get("created_at") or "not stored")


def _duration_stamp(record):
    raw = _timestamp(record)
    stamp = re.sub(r"[^0-9]", "", raw)[:14] or "undated"
    return stamp


def _snippet(hit, transcript):
    text = hit.get("transcript_snippet")
    if text:
        return text
    phrase = str(hit.get("matched_phrase") or "")
    if phrase and transcript:
        position = str(transcript).lower().find(phrase.lower())
        if position >= 0:
            start = max(0, position - 70)
            end = min(len(transcript), position + len(phrase) + 70)
            return str(transcript)[start:end]
    return "-"


# ---------------------------------------------------------------------------
# PDF document
# ---------------------------------------------------------------------------

class _Report(FPDF):
    """FPDF subclass that keeps the page furniture in one place."""

    def __init__(self):
        face = devanagari_font()
        super().__init__(orientation="P", unit="mm", format="A4")
        self.family = "Body" if face else "Helvetica"
        self.generated = datetime.date.today().strftime("%d %b %Y")
        pdf = self
        pdf.set_margins(15, 15, 15)
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_title("CloneGuard evidence report")
        pdf.set_author("CloneGuard")
        pdf.set_creator("CloneGuard " + config.APP_VERSION)
        if face:
            pdf.add_font("Body", "", face["regular"])
            pdf.add_font("Body", "B", face["bold"])
            try:
                pdf.set_text_shaping(True)
            except Exception:
                # No uharfbuzz: glyphs still render, but complex-script shaping
                # is limited to what the font's own cmap provides.
                pass
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_text_color(*INK)

    # -- furniture ---------------------------------------------------------

    def footer(self):
        pdf = self
        pdf.set_y(-14)
        pdf.set_draw_color(*RULE)
        pdf.line(15, pdf.get_y() - 2, 195, pdf.get_y() - 2)
        pdf.set_font(self.family, "", 7)
        pdf.set_text_color(*MUTED)
        pdf.cell(60, 5, _clean("Generated %s" % self.generated))
        pdf.cell(60, 5, "Local interface, cloud inference via Gnani", align="C")
        pdf.cell(
            60,
            5,
            _clean("Page %d of {nb}" % pdf.page_no()),
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_text_color(*INK)

    # -- primitives --------------------------------------------------------

    def run(self, text, size=9, style="", line_h=4.6, color=None):
        pdf = self
        pdf.set_font(self.family, style, size)
        if color:
            pdf.set_text_color(*color)
        pdf.multi_cell(pdf.epw, line_h, _text(text), align="L")
        if color:
            pdf.set_text_color(*INK)

    def space(self, height):
        if self.get_y() + height > self.h - self.b_margin:
            self.add_page()
        else:
            self.ln(height)

    def section(self, title, note=None):
        pdf = self
        if pdf.get_y() + 16 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.ln(2)
        pdf.set_font(self.family, "B", 11)
        pdf.set_text_color(*ACCENT)
        pdf.cell(pdf.epw, 6, _clean(title), new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y()
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.5)
        pdf.line(15, y, 33, y)
        pdf.set_line_width(0.2)
        pdf.set_draw_color(*RULE)
        pdf.set_text_color(*INK)
        pdf.ln(2.2)
        if note:
            pdf.set_font(self.family, "", 8)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(pdf.epw, 4, _text(note))
            pdf.set_text_color(*INK)
            pdf.ln(0.5)

    def table(self, widths, headers, rows, aligns=None, sizes=None, marks=None):
        pdf = self
        aligns = aligns or ["L"] * len(widths)
        sizes = sizes or [7.8] * len(widths)
        line_h = 4.0

        def draw_header():
            pdf.set_font(self.family, "B", 7.8)
            pdf.set_fill_color(*ACCENT)
            pdf.set_text_color(255, 255, 255)
            x, y = pdf.l_margin, pdf.get_y()
            for width, header in zip(widths, headers):
                pdf.rect(x, y, width, 6, style="F")
                pdf.set_xy(x + 1.4, y + 1.1)
                pdf.cell(width - 2.8, 4, _clean(header))
                x += width
            pdf.set_xy(pdf.l_margin, y + 6)
            pdf.set_text_color(*INK)

        draw_header()
        for index, row in enumerate(rows):
            heights = []
            for width, value, size in zip(widths, row, sizes):
                pdf.set_font(self.family, "", size)
                heights.append(
                    pdf.multi_cell(
                        width,
                        line_h,
                        _text(str(value)),
                        dry_run=True,
                        output="HEIGHT",
                        padding=1.4,
                    )
                )
            row_h = max(heights) + 1.2
            if pdf.get_y() + row_h > pdf.h - pdf.b_margin:
                pdf.add_page()
                draw_header()
            x, y = pdf.l_margin, pdf.get_y()
            fill = marks is not None and index in marks
            for width, value, align, size in zip(widths, row, aligns, sizes):
                if fill:
                    pdf.set_fill_color(*TINT)
                    pdf.rect(x, y, width, row_h, style="F")
                pdf.set_font(self.family, "", size)
                pdf.set_xy(x, y + 0.4)
                pdf.multi_cell(
                    width,
                    line_h,
                    _text(str(value)),
                    align=align,
                    padding=1.4,
                )
                x += width
            x = pdf.l_margin
            pdf.set_draw_color(*RULE)
            for width in widths:
                pdf.rect(x, y, width, row_h)
                x += width
            pdf.set_xy(pdf.l_margin, y + row_h)

    # -- composed blocks ---------------------------------------------------

    def title_block(self, record):
        pdf = self
        pdf.set_fill_color(*ACCENT)
        pdf.rect(15, 13.5, 26, 1.8, style="F")
        pdf.ln(2)
        pdf.set_font(self.family, "B", 19)
        pdf.set_text_color(*INK)
        pdf.cell(pdf.epw, 10, "CloneGuard evidence report", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(self.family, "", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.multi_cell(
            pdf.epw,
            4.4,
            _clean(
                "Evidence for one checked call, built from the stored record. "
                "Exporting this report runs no new analysis."
            ),
        )
        pdf.set_text_color(*INK)
        pdf.ln(2)
        meta = [
            ("Check id", str(record.get("id") or "not stored")),
            ("Checked at", _timestamp(record)),
            ("App version", config.APP_VERSION),
        ]
        for label, value in meta:
            pdf.set_font(self.family, "B", 8.5)
            pdf.cell(30, 4.8, _clean(label))
            pdf.set_font(self.family, "", 8.5)
            pdf.multi_cell(pdf.epw - 30, 4.8, _text(value))
        pdf.ln(1)

    def verdict_box(self, sentence):
        pdf = self
        if pdf.get_y() + 24 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.set_font(self.family, "", 11)
        height = pdf.multi_cell(
            pdf.epw - 8,
            5.6,
            _text(sentence),
            dry_run=True,
            output="HEIGHT",
            padding=3,
        )
        x, y = pdf.l_margin, pdf.get_y()
        pdf.set_fill_color(*TINT)
        pdf.rect(x, y, pdf.epw, height + 3, style="F")
        pdf.set_fill_color(*ACCENT)
        pdf.rect(x, y, 1.6, height + 3, style="F")
        pdf.set_xy(x + 4, y + 1.5)
        pdf.set_text_color(*INK)
        pdf.multi_cell(pdf.epw - 8, 5.6, _text(sentence), padding=3)
        pdf.set_xy(pdf.l_margin, y + height + 3)


def _layer1_rows(record):
    layer1 = record.get("layer1") or {}
    comparisons = layer1.get("comparisons") or []
    rows = []
    marks = set()
    for index, row in enumerate(comparisons):
        cosine = row.get("cosine")
        rows.append(
            (
                str(row.get("name") or "-"),
                str(row.get("role") or "-"),
                "-" if cosine is None else "%.4f" % float(cosine),
                "%.2f" % float(row.get("threshold", layer1.get("threshold") or config.THRESHOLD)),
                str(row.get("verdict") or "-"),
                "target" if row.get("target") else "",
            )
        )
        if row.get("target"):
            marks.add(index)
    return rows, marks


def _layer1_note(record):
    layer1 = record.get("layer1") or {}
    if not (layer1.get("comparisons") or []):
        return "No voiceprints were enrolled when this check ran, so Layer 1 was not scored."
    if not layer1.get("comparable", True):
        return "Layer 1 was not scored: no enrolled voiceprint matched the claim."
    return "The row marked target is the voiceprint the identity claim resolved to."


def _claim_text(record):
    claim = record.get("claim") or {}
    phrase = claim.get("detected_phrase")
    resolved = claim.get("voiceprint_id")
    if phrase:
        role = claim.get("role")
        if resolved:
            detail = "%s, voiceprint %s" % (role or resolved, resolved)
        else:
            detail = "not enrolled"
        return "Detected phrase: \"%s\"  ->  resolved voiceprint: %s" % (
            phrase,
            detail,
        )
    note = claim.get("note") or "no claim detected"
    return "no claim detected. %s" % note if not str(note).startswith("no claim") else note


def _composite_rows(record):
    layer1 = record.get("layer1") or {}
    hits = (record.get("layer2") or {}).get("hits") or []
    threshold = layer1.get("threshold", config.THRESHOLD)
    l1_risk = score_mod.layer1_risk(
        layer1.get("best_cosine") if layer1.get("comparable", True) else None,
        threshold,
    )
    l2_risk = score_mod.layer2_risk(hits)
    band = record.get("band")
    rows = [
        ("Layer 1 risk", "not comparable" if l1_risk is None else "%.4f" % l1_risk),
        ("Layer 2 risk", "%.4f" % l2_risk),
        ("Weights", "Layer 1 %.2f / Layer 2 %.2f" % (config.W_L1, config.W_L2)),
        ("Composite score", "%s / 100" % record.get("composite", "-")),
        ("Band", BAND_LABELS.get(band, str(band or "-"))),
    ]
    if l1_risk is None:
        rows.append(("Method", "Layer 2 alone, rescaled to 0-100"))
    return rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def render_incident_pdf(record, out_dir=None):
    """Write one A4 PDF for a stored check and return its absolute path."""
    if not isinstance(record, dict):
        raise TypeError("record must be a dict from data\\incidents.json")

    doc = _Report()
    pdf = doc
    doc.title_block(record)

    # Caller audio
    facts = audio_facts(record)
    doc.section("Caller audio")
    doc.table(
        (58, 42, 40, 40),
        ("File name", "Duration", "Sample rate", "Source"),
        [(facts["name"], facts["duration"], facts["rate"], facts["source"])],
        sizes=(7.6, 7.8, 7.8, 7.8),
    )

    # Layer 1
    doc.section("Layer 1 evidence: voiceprint comparison")
    rows, marks = _layer1_rows(record)
    if rows:
        doc.table(
            (52, 34, 24, 24, 32, 14),
            ("Voiceprint", "Role", "Cosine", "Threshold", "Result", "Target"),
            rows,
            aligns=("L", "L", "R", "R", "L", "L"),
            marks=marks,
        )
        doc.run(_layer1_note(record), size=7.8, line_h=3.8, color=MUTED)
    else:
        doc.run(_layer1_note(record), size=8.5, line_h=4.2)
    doc.run("Layer 1 result: " + str((record.get("layer1") or {}).get("label") or "-"), size=8.5)

    # Claimed identity
    doc.section("Claimed identity")
    doc.run(_claim_text(record), size=8.8, line_h=4.4)

    # Layer 2
    doc.section("Layer 2 evidence: Hinglish scam-pattern scan")
    hits = (record.get("layer2") or {}).get("hits") or []
    transcript = record.get("transcript") or ""
    if hits:
        rows = []
        for hit in hits:
            rows.append(
                (
                    str(hit.get("category") or "-"),
                    str(hit.get("matched_phrase") or "-"),
                    _snippet(hit, transcript),
                    str(hit.get("severity") or "-"),
                )
            )
        doc.table(
            (46, 40, 74, 20),
            ("Category", "Matched phrase", "Transcript snippet", "Severity"),
            rows,
            aligns=("L", "L", "L", "L"),
            sizes=(7.5, 7.5, 7.2, 7.5),
        )
    else:
        doc.run("No patterns matched.", size=9)
        doc.run(
            "The phrase list did not match this transcript. See Limitations: "
            "that is not a statement about the call.",
            size=7.8,
            line_h=3.8,
            color=MUTED,
        )

    if transcript:
        doc.section("Transcript excerpt (Prisma)")
        excerpt = str(transcript)
        if len(excerpt) > 500:
            excerpt = excerpt[:497] + "..."
        doc.run(excerpt, size=8.3, line_h=4.4)

    # Composite
    doc.section("Composite result")
    doc.table(
        (44, 136),
        ("Part", "Stored value"),
        _composite_rows(record),
        sizes=(8, 8),
    )

    # Verdict
    doc.section("Verdict")
    doc.verdict_box(str(record.get("verdict_sentence") or "No verdict sentence was stored."))
    doc.run(
        "The sentence above is the stored verdict, identical to the one shown on screen.",
        size=7.8,
        line_h=3.8,
        color=MUTED,
    )

    # Limitations
    doc.section("Limitations")
    for index, item in enumerate(LIMITATIONS, start=1):
        doc.run("%d. %s" % (index, item), size=8.3, line_h=4.2)

    face = devanagari_font()
    if face and has_devanagari(transcript):
        doc.run(
            "Devanagari text is rendered with %s, embedded as a subset in this file."
            % face["name"],
            size=7.4,
            line_h=3.6,
            color=MUTED,
        )
    elif not face:
        doc.run(FALLBACK_NOTE, size=7.4, line_h=3.6, color=MUTED)

    # Ensure the footer lands on every page.
    pdf.set_auto_page_break(auto=True, margin=18)

    if out_dir is None:
        out_dir = REPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    check = str(record.get("id") or "check")
    stamp = _duration_stamp(record)
    name = re.sub(r"[^0-9A-Za-z._-]+", "_", "evidence_%s_%s.pdf" % (check, stamp))
    path = os.path.abspath(os.path.join(out_dir, name))
    pdf.output(path)
    return path


if __name__ == "__main__":
    import json

    with open(config.INCIDENTS_PATH, "r", encoding="utf-8") as handle:
        stored = json.load(handle)
    if not stored:
        raise SystemExit("no incident records in %s" % config.INCIDENTS_PATH)
    written = render_incident_pdf(stored[-1])
    print(written)
    print("%d bytes" % os.path.getsize(written))
