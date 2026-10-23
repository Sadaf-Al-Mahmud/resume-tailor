#!/usr/bin/env python3
"""
build.py -- Consolidated resume/CV build + verify pipeline (v3).

Single entry point replacing the old generate -> convert -> pdfinfo ->
pdftoppm -> manually-inspect -> regenerate chain. One call does:
  1. Validate the content JSON (located errors, not a bare "invalid JSON").
  2. Build a clean, single-column .docx (real bullets, real hyperlinks,
     dynamic tab-stop date alignment, keep-with-next on headings/titles,
     label+value Skills rendering, normalized dates).
  3. Convert to PDF, count pages, verify the font that actually rendered.
  4. If over the target page count: apply free mechanical page-fit levers
     (smaller body size, smaller margins) automatically and rebuild --
     no content lost, no round trip spent on something purely mechanical.
     If still over after that, report back which cut-first entries exist
     and how much overage remains, WITHOUT deciding what to cut itself --
     that judgment call stays with the assistant/user.
  5. If posting_terms were supplied: a deterministic keyword-coverage
     check (literal match, required vs preferred) -- the single source of
     truth for keyword coverage; no separate, competing judgment score.
  6. If any entry supplied source_numbers: a claims-trace check -- every
     numeric token in that entry's drafted text must appear in its
     source_numbers, or it's flagged as unverified (a concrete,
     script-enforced version of "never invent a number").
  7. Clean stale output (old renders in the output directory) before
     writing new files, so nothing stale gets mistaken for current output.

Prints ONE compact JSON result to stdout -- page count, paper size, font
check, keyword coverage, claims-trace issues, what fit levers were
applied, and (only if still over length) cut-first candidates -- so the
assistant reads one small structured result instead of stitching together
several command outputs.

Usage:
    python build.py <content.json> <output_base> [options]

    <output_base> is a path WITHOUT extension, e.g. "out/resume" ->
    produces out/resume.docx and out/resume.pdf (and out/resume.txt only
    with --text).

Options:
    --paper A4|Letter   Force a page size. If omitted, inferred from
                        content.json's "target_country" (see PAPER
                        logic below) and defaults to A4 -- A4/ISO 216 is
                        the page size most of the world uses; Letter is
                        the primary size in a short list of countries (see
                        LETTER_COUNTRIES). When the country is unknown or
                        not on that list, A4 is used and this is noted in
                        the result (paper_inferred) so the assistant can
                        confirm rather than silently guess for an edge case.
    --body-size PT      Starting body text size (default 10.5).
    --margin IN         Starting page margin, all sides (default 0.65).
    --max-pages N       Target page count: 1 (default), 2, or 3 -- no other
                        value is accepted. 3 is a deliberate last resort for
                        a CV tailored to an actual posting (posting_terms
                        present) or for a fully general base CV with no role
                        in mind (content "cv_kind": "base_general"). It is
                        REJECTED (a clean "status": "error" result, not
                        built) for any other content -- e.g. a base CV with
                        no cv_kind, or "cv_kind": "base_role" (a base CV
                        aimed at a role/field), which stays at 2 pages max.
    --no-auto-fit       Disable the automatic font/margin step-down;
                        fail with the overage reported instead.
    --text              Also write a plain-text sibling (off by default).
    --filename-stub S   Override the output basename stub used in the
                        JSON result's "files" field (cosmetic only).

Content JSON schema:
{
  "name": "Full Name",
  "contact_items": ["email@example.com", "+1 555 0100",
                     "linkedin.com/in/handle", "github.com/handle",
                     "City, Country"],
  "target_country": "Canada",            // optional; the country/place the user
                                          // typed (bare country or "City, Country");
                                          // informs paper size only
  "summary": "One or two sentences, or null to omit",
  "photo_path": null,                     // real user-supplied photo only
  "cv_kind": "tailored",                  // optional: "tailored" | "base_role" |
                                          // "base_general". Only "base_general" (a
                                          // base CV with NO role in mind) may use
                                          // --max-pages 3 without posting_terms.
  "posting_terms": [                      // optional, tailored path only
    {"term": "SQL", "required": true},
    {"term": "data visualization", "required": false}
  ],
  "sections": [
    {
      "heading": "EDUCATION",
      "entries": [
        {
          "title": "BBA, Supply Chain Management",
          "subtitle": "State University",
          "date": "Expected 2027",
          "tools": null,                  // optional "Tools: X, Y, Z" line
          "link": null,                   // optional hyperlink on entry
          "tier": "strong",                // "protected" | "strong" | "cut-first"
          "source_numbers": ["2027"],      // optional, for claims-trace
          "bullets": ["Relevant coursework: ..."]
        },
        {
          "label": "Data & Analytics",     // Skills-style entry instead
          "values": "Excel, Looker Studio, GA4"
        }
      ]
    }
  ],
  "references_list": [                    // optional people-references section
    {"name": "Dr. Jane Doe", "title": "Professor", "contact": "jane@school.edu"}
  ]
}

Notes:
- "tier" drives nothing in the script automatically (tiering is a content
  decision made upstream) except: (a) it is used purely as a label echoed
  back in cut-first candidate reporting when the page doesn't fit, and
  (b) entries tagged "protected" are never suggested as cut candidates.
- "photo_path" must be a real file the user supplied -- never generate an
  image of the user. Rendered small and inline with the header block, not
  as a full-width paragraph.
- Every number appearing in an entry's title/subtitle/bullets/tools is
  checked against that entry's own "source_numbers" list, if provided.
  Entries that don't provide source_numbers are skipped (no false
  positives) -- this is a heuristic safety net, not a perfect guarantee,
  and the assistant should still apply ordinary judgment.
"""

import sys
import os
import re
import json
import glob
import shutil
import argparse
import subprocess
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


class BuildError(Exception):
    """Raised for any build-time failure (bad photo file, missing external
    tool, a malformed document LibreOffice can't convert, etc.) that should
    surface as the script's own clean JSON error result instead of an
    uncaught Python traceback -- the script's contract is always ONE JSON
    result on stdout, success or failure."""
    pass


FONT_NAME = "Calibri"
NAME_SIZE = Pt(20)
HEADING_SIZE = Pt(11.5)
CONTACT_SIZE = Pt(9.5)
SMALL_SIZE = Pt(9)
GRAY = RGBColor(0x40, 0x40, 0x40)
ACCENT = "1F4E79"  # single muted accent color, reused everywhere
MAX_CONTACT_ITEMS_PER_LINE = 3

# Letter (8.5x11in) is the primary paper size in a small set of countries and
# territories; nearly everywhere else uses A4 (ISO 216). The set below is the
# list of primary-Letter countries/territories from the Unicode CLDR paper-size
# data, as summarized on Wikipedia's "Letter (paper size)" page. Anything not
# matched defaults to A4, and the build result reports that the size was
# inferred (paper_inferred) so an unusual or ambiguous place is visible rather
# than silently assumed. Names are compared after normalization (lowercase, no
# periods, no leading "the"), so "U.S.A.", "The United States" and "usa" all match.
LETTER_COUNTRIES = {
    "united states", "united states of america", "usa", "us",
    "canada", "mexico", "philippines", "puerto rico",
    "belize", "chile", "colombia", "costa rica", "el salvador",
    "guatemala", "nicaragua", "panama", "venezuela",
}

PAGE_SIZES = {
    "A4": (Inches(8.27), Inches(11.69)),
    "LETTER": (Inches(8.5), Inches(11.0)),
}

# The automatic fit-down step: how far to shrink body size/margin from
# WHATEVER was requested (not a fixed absolute target -- see main()), and
# the floor each is never shrunk past so the page stays legible/printable.
FIT_STEP_BODY_PT = 0.5
FIT_STEP_MARGIN_IN = 0.05
FIT_MIN_BODY_PT = 9.0
FIT_MIN_MARGIN_IN = 0.4


def _normalize_place(text):
    s = text.lower().replace(".", "")
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("the "):
        s = s[4:]
    return s


def infer_paper(content, explicit):
    if explicit:
        return explicit.upper()
    # target_country arrives as free text typed by a user (a bare country, or
    # "City, Country", or "Remote (Country)"), so it's split on common
    # separators and each piece is checked on its own -- an exact-match on the
    # whole string would silently fall through to A4 for "Toronto, Canada".
    raw = content.get("target_country") or ""
    for part in re.split(r"[,;/|()]", str(raw)):
        if _normalize_place(part) in LETTER_COUNTRIES:
            return "LETTER"
    return "A4"


# ---------------------------------------------------------------------------
# Validation (located errors)
# ---------------------------------------------------------------------------

def validate(content):
    errors = []
    if not isinstance(content, dict):
        return ["Top level of content JSON must be an object."]
    if not content.get("name"):
        errors.append("Missing required field: \"name\".")
    sections = content.get("sections")
    if not sections:
        errors.append("Missing or empty required field: \"sections\".")
    elif not isinstance(sections, list):
        errors.append("\"sections\" must be a list.")
    else:
        for si, section in enumerate(sections):
            if not isinstance(section, dict):
                errors.append(f"sections[{si}] must be an object.")
                continue
            if not section.get("heading"):
                errors.append(f"sections[{si}] is missing \"heading\".")
            entries = section.get("entries")
            if not isinstance(entries, list):
                errors.append(f"sections[{si}] (\"{section.get('heading','?')}\") is missing a valid \"entries\" list.")
                continue
            for ei, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    errors.append(f"sections[{si}].entries[{ei}] must be an object.")
                    continue
                is_skills_style = "label" in entry and "values" in entry
                is_normal_style = "title" in entry
                if not is_skills_style and not is_normal_style:
                    errors.append(
                        f"sections[{si}].entries[{ei}] needs either \"title\" "
                        f"(normal entry) or \"label\"+\"values\" (skills-style entry)."
                    )
                tier = entry.get("tier")
                if tier is not None and tier not in ("protected", "strong", "cut-first"):
                    errors.append(
                        f"sections[{si}].entries[{ei}] has an invalid \"tier\": "
                        f"{tier!r} (must be protected, strong, or cut-first)."
                    )
                # "bullets" and "source_numbers" are list-shaped fields that
                # are easy to accidentally pass as a plain string (e.g.
                # "source_numbers": "25" instead of ["25"]). A string isn't
                # rejected by Python's set()/iteration, so without this check
                # the mistake doesn't error -- it silently produces a
                # confusing, wrong claims-trace result (each character
                # treated as its own "number") instead of a clear fix-your-
                # input message.
                bullets = entry.get("bullets")
                if bullets is not None and not isinstance(bullets, list):
                    errors.append(
                        f"sections[{si}].entries[{ei}] \"bullets\" must be a "
                        f"list of strings (got {type(bullets).__name__})."
                    )
                source_numbers = entry.get("source_numbers")
                if source_numbers is not None and not isinstance(source_numbers, list):
                    errors.append(
                        f"sections[{si}].entries[{ei}] \"source_numbers\" must be a "
                        f"list of strings (got {type(source_numbers).__name__}) -- "
                        f"e.g. [\"25\"], not \"25\"."
                    )
    target_country = content.get("target_country")
    if target_country is not None and not isinstance(target_country, str):
        errors.append(f"\"target_country\" must be a string (got {type(target_country).__name__}).")
    contact_items = content.get("contact_items")
    if contact_items is not None and not isinstance(contact_items, list):
        errors.append(f"\"contact_items\" must be a list (got {type(contact_items).__name__}).")
    references_list = content.get("references_list")
    if references_list is not None:
        if not isinstance(references_list, list):
            errors.append(f"\"references_list\" must be a list (got {type(references_list).__name__}).")
        else:
            for ri, r in enumerate(references_list):
                if not isinstance(r, dict):
                    errors.append(f"references_list[{ri}] must be an object.")
    cv_kind = content.get("cv_kind")
    if cv_kind is not None and cv_kind not in ("tailored", "base_role", "base_general"):
        errors.append(f"\"cv_kind\" must be tailored, base_role, or base_general (got {cv_kind!r}).")
    posting_terms = content.get("posting_terms")
    if posting_terms is not None:
        if not isinstance(posting_terms, list):
            errors.append("\"posting_terms\" must be a list if present.")
        else:
            for ti, t in enumerate(posting_terms):
                if not isinstance(t, dict) or "term" not in t:
                    errors.append(f"posting_terms[{ti}] must be an object with a \"term\" field.")
    return errors


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

MONTHS = {
    "jan": "Jan", "january": "Jan", "feb": "Feb", "february": "Feb",
    "mar": "Mar", "march": "Mar", "apr": "Apr", "april": "Apr",
    "may": "May", "jun": "Jun", "june": "Jun", "jul": "Jul", "july": "Jul",
    "aug": "Aug", "august": "Aug", "sep": "Sep", "sept": "Sep",
    "september": "Sep", "oct": "Oct", "october": "Oct",
    "nov": "Nov", "november": "Nov", "dec": "Dec", "december": "Dec",
}
SEASON_TO_MONTH = {
    # Explicitly approximate -- flagged as such wherever used.
    "spring": "Mar", "summer": "Jun", "fall": "Sep", "autumn": "Sep",
    "winter": "Dec",
}


def normalize_date(raw):
    """Returns (normalized_string, was_approximated). Never raises --
    anything it can't confidently parse is returned unchanged with a flag."""
    if not raw or not isinstance(raw, str):
        return raw, False
    s = raw.strip()
    low = s.lower()

    # Range like "June 2024 - Dec 2025" or "2025 - Oct 2026" -> normalize
    # each side independently.
    for sep in (" - ", "-", " to ", "–", "—"):
        if sep in s and sep.strip():
            parts = s.split(sep)
            if len(parts) == 2:
                left, lflag = normalize_date(parts[0].strip())
                right, rflag = normalize_date(parts[1].strip())
                return f"{left} - {right}", (lflag or rflag)

    m = re.match(r"^(expected\s+)?([a-zA-Z]+)\s+(\d{4})$", s, re.IGNORECASE)
    if m:
        prefix, word, year = m.groups()
        word_low = word.lower()
        if word_low in MONTHS:
            out = f"{MONTHS[word_low]} {year}"
            return (f"Expected {out}" if prefix else out), False
        if word_low in SEASON_TO_MONTH:
            out = f"~{SEASON_TO_MONTH[word_low]} {year}"
            return (f"Expected {out}" if prefix else out), True

    if re.match(r"^(expected\s+)?\d{4}$", low):
        return s, False

    # Couldn't confidently parse -- return as-is, flagged.
    return s, True


# ---------------------------------------------------------------------------
# DOCX helpers
# ---------------------------------------------------------------------------

def set_base_font(doc, body_size):
    style = doc.styles["Normal"]
    style.font.name = FONT_NAME
    style.font.size = body_size
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), FONT_NAME)
    rfonts.set(qn("w:ascii"), FONT_NAME)
    rfonts.set(qn("w:hAnsi"), FONT_NAME)


def ensure_heading_style(doc):
    """A real semantic heading style (not just bold text), so a parser
    keying off heading structure -- not only bold+border -- also sees it."""
    styles = doc.styles
    name = "CVSectionHeading"
    if name in [s.name for s in styles]:
        return styles[name]
    style = styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.base_style = styles["Heading 2"]
    style.font.name = FONT_NAME
    style.font.size = HEADING_SIZE
    style.font.bold = True
    style.font.color.rgb = RGBColor.from_string(ACCENT)
    style.paragraph_format.space_before = Pt(10)
    style.paragraph_format.space_after = Pt(3)
    style.paragraph_format.keep_with_next = True
    return style


def set_core_properties(doc, name):
    props = doc.core_properties
    props.author = name or "Candidate"
    props.last_modified_by = name or "Candidate"
    props.title = f"{name} - Resume" if name else "Resume"
    props.comments = ""


def add_bottom_border(paragraph, color=ACCENT, size="6"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), size)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_hyperlink(paragraph, url, text, size_pt):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rfonts = OxmlElement("w:rFonts")
    rfonts.set(qn("w:ascii"), FONT_NAME)
    rpr.append(rfonts)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), ACCENT)
    rpr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    rpr.append(underline)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size_pt.pt * 2)))
    rpr.append(sz)
    new_run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def classify_contact_item(item):
    if "@" in item and " " not in item:
        return item, f"mailto:{item}"
    lowered = item.lower()
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return item, item
    if "linkedin.com" in lowered or "github.com" in lowered:
        return item, f"https://{item}"
    return item, None


def add_contact_block(doc, items):
    if not items:
        return
    lines = [items[i:i + MAX_CONTACT_ITEMS_PER_LINE]
             for i in range(0, len(items), MAX_CONTACT_ITEMS_PER_LINE)]
    for line_items in lines:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        for idx, raw in enumerate(line_items):
            text, link = classify_contact_item(raw)
            if link:
                add_hyperlink(p, link, text, CONTACT_SIZE)
            else:
                run = p.add_run(text)
                run.font.size = CONTACT_SIZE
                run.font.color.rgb = GRAY
            if idx != len(line_items) - 1:
                sep = p.add_run("   |   ")
                sep.font.size = CONTACT_SIZE
                sep.font.color.rgb = GRAY


def add_heading(doc, text, heading_style):
    p = doc.add_paragraph(style=heading_style)
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = HEADING_SIZE
    run.font.name = FONT_NAME
    run.font.color.rgb = RGBColor.from_string(ACCENT)
    add_bottom_border(p)
    return p


def right_tab_position(section):
    """Computed from the ACTUAL page width and margins at build time --
    never a hardcoded constant. This is the direct fix for the confirmed
    bug where a fixed 7.2in stop only lined up with one specific
    page-size/margin combination and silently overhung the margin for
    any other (A4, or a tightened --margin page-fit step)."""
    usable = section.page_width - section.left_margin - section.right_margin
    return usable


def add_entry(doc, entry, is_last_in_doc, tab_pos, date_warnings, mark_strongest):
    # Skills-style entry: "Label: values" on one line, label bold.
    if "label" in entry and "values" in entry:
        p = doc.add_paragraph()
        label_run = p.add_run(f"{entry['label']}: ")
        label_run.bold = True
        p.add_run(entry.get("values", ""))
        # Zero trailing space on the last entry in the document, same rule
        # every other entry type follows -- a Skills-style entry landing
        # last used to keep a stray 4pt here instead of 0pt.
        p.paragraph_format.space_after = Pt(0) if is_last_in_doc else Pt(6)
        return

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.tab_stops.add_tab_stop(tab_pos, WD_TAB_ALIGNMENT.RIGHT)

    title_run = p.add_run(entry.get("title", ""))
    title_run.bold = True
    # The single strongest (protected-tier, first-such) entry gets a
    # visual anchor via the shared accent color on its title -- so the
    # eye catches it first, without introducing a second color or
    # breaking ATS-safe plain-text structure.
    if mark_strongest:
        title_run.font.color.rgb = RGBColor.from_string(ACCENT)

    raw_date = entry.get("date")
    if raw_date:
        norm_date, approximated = normalize_date(raw_date)
        if approximated:
            date_warnings.append(f"{entry.get('title','(untitled)')}: {raw_date!r} -> {norm_date!r}")
        # Two real spaces before the tab: a PDF viewer/extractor that drops the
        # positional gap of a right-aligned tab would otherwise glue the date
        # onto the end of the title ("ManagementExpected 2027").
        p.add_run("  \t" + norm_date)

    link = entry.get("link")
    if entry.get("subtitle") or link:
        sub_p = doc.add_paragraph()
        sub_p.paragraph_format.space_after = Pt(2)
        sub_p.paragraph_format.keep_with_next = True
        if entry.get("subtitle"):
            sub_run = sub_p.add_run(entry["subtitle"])
            sub_run.italic = True
        if link:
            if entry.get("subtitle"):
                sub_p.add_run("  —  ")
            add_hyperlink(sub_p, link, link.replace("https://", "").replace("http://", ""), SMALL_SIZE)

    bullets = entry.get("bullets", []) or []
    for i, bullet in enumerate(bullets):
        bp = doc.add_paragraph(style="List Bullet")
        if i == 0:
            bp.paragraph_format.keep_with_next = len(bullets) > 1
        last_bullet = (i == len(bullets) - 1)
        if last_bullet and not entry.get("tools"):
            bp.paragraph_format.space_after = Pt(0) if is_last_in_doc else Pt(8)
        else:
            bp.paragraph_format.space_after = Pt(2)
        bp.add_run(bullet)

    tools = entry.get("tools")
    if tools:
        tp = doc.add_paragraph()
        tp.paragraph_format.space_after = Pt(0) if is_last_in_doc else Pt(8)
        label_run = tp.add_run("Tools: ")
        label_run.bold = True
        label_run.font.size = SMALL_SIZE
        val_run = tp.add_run(tools)
        val_run.font.size = SMALL_SIZE

    if not bullets and not tools:
        p.paragraph_format.space_after = Pt(0) if is_last_in_doc else Pt(8)


def add_references_section(doc, refs, heading_style):
    if not refs:
        return
    add_heading(doc, "References", heading_style)
    for r in refs:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        name_run = p.add_run(r.get("name", ""))
        name_run.bold = True
        extra = " — ".join(x for x in [r.get("title"), r.get("contact")] if x)
        if extra:
            p.add_run(f", {extra}")


def standard_bullets(doc):
    """Use a plain Unicode bullet (U+2022) in the body font for 'List Bullet',
    instead of the template's Symbol-font private-use glyph."""
    try:
        style = doc.styles["List Bullet"]
        num_id = style.element.pPr.numPr.numId.val
        numbering = doc.part.numbering_part.element
        abs_id = None
        for num in numbering.findall(qn("w:num")):
            if num.get(qn("w:numId")) == str(num_id):
                abs_id = num.find(qn("w:abstractNumId")).get(qn("w:val"))
        for absn in numbering.findall(qn("w:abstractNum")):
            if absn.get(qn("w:abstractNumId")) == abs_id:
                lvl = absn.find(qn("w:lvl"))
                lvl.find(qn("w:lvlText")).set(qn("w:val"), "\u2022")
                rpr = lvl.find(qn("w:rPr"))
                if rpr is None:
                    rpr = OxmlElement("w:rPr")
                    lvl.append(rpr)
                for old in rpr.findall(qn("w:rFonts")):
                    rpr.remove(old)
                rf = OxmlElement("w:rFonts")
                for k in ("ascii", "hAnsi", "cs", "eastAsia"):
                    rf.set(qn("w:" + k), FONT_NAME)
                rpr.insert(0, rf)
    except Exception:
        # Falls back to the template's own bullet (still a real list item);
        # never fail a build over the bullet glyph.
        pass


def build_docx(content, out_path, body_size, margin, paper):
    doc = Document()
    pw, ph = PAGE_SIZES[paper]
    for section in doc.sections:
        section.page_width = pw
        section.page_height = ph
        section.top_margin = margin
        section.bottom_margin = margin
        section.left_margin = margin
        section.right_margin = margin
    set_base_font(doc, body_size)
    set_core_properties(doc, content.get("name", ""))
    heading_style = ensure_heading_style(doc)
    standard_bullets(doc)

    name_p = doc.add_paragraph()
    name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_p.paragraph_format.keep_with_next = True
    name_run = name_p.add_run(content.get("name", ""))
    name_run.bold = True
    name_run.font.size = NAME_SIZE
    name_run.font.name = FONT_NAME
    name_run.font.color.rgb = RGBColor.from_string(ACCENT)

    add_contact_block(doc, content.get("contact_items", []))

    photo_path = content.get("photo_path")
    if photo_path and os.path.isfile(photo_path):
        # Small, fixed-width, inline with the header block -- not a
        # full-width paragraph (which was confirmed to cost over an inch
        # on a one-page CV).
        pic_p = doc.add_paragraph()
        pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic_p.paragraph_format.space_after = Pt(4)
        run = pic_p.add_run()
        try:
            run.add_picture(photo_path, width=Inches(1.0))
        except Exception as e:
            raise BuildError(
                f'photo_path "{photo_path}" exists but could not be read as an '
                f"image ({e.__class__.__name__}: {e}). Confirm it's a real image "
                f"file (JPEG/PNG/etc.), or omit photo_path."
            )

    if content.get("summary"):
        summary_p = doc.add_paragraph()
        summary_p.paragraph_format.space_after = Pt(6)
        summary_p.paragraph_format.space_before = Pt(4)
        # Regular weight, not italic -- italic is measurably harder to
        # skim and summary is the single most-read line on the page.
        summary_p.add_run(content["summary"])

    tab_pos = right_tab_position(doc.sections[0])
    date_warnings = []

    sections = content.get("sections", [])
    strongest_marked = False
    for s_idx, section in enumerate(sections):
        add_heading(doc, section.get("heading", "SECTION"), heading_style)
        entries = section.get("entries", [])
        for e_idx, entry in enumerate(entries):
            is_last_in_doc = (s_idx == len(sections) - 1) and (e_idx == len(entries) - 1)
            mark_strongest = (not strongest_marked) and entry.get("tier") == "protected" and "title" in entry
            if mark_strongest:
                strongest_marked = True
            add_entry(doc, entry, is_last_in_doc, tab_pos, date_warnings, mark_strongest)

    add_references_section(doc, content.get("references_list"), heading_style)

    doc.save(out_path)
    return date_warnings


def write_plain_text(content, txt_path):
    lines = [content.get("name", ""), ""]
    lines.append(" | ".join(content.get("contact_items", [])))
    lines.append("")
    if content.get("summary"):
        lines.append(content["summary"])
        lines.append("")
    for section in content.get("sections", []):
        heading = section.get("heading", "SECTION")
        lines.append(heading.upper())
        lines.append("-" * len(heading))
        for entry in section.get("entries", []):
            if "label" in entry and "values" in entry:
                lines.append(f"{entry['label']}: {entry['values']}")
                continue
            header = entry.get("title", "")
            if entry.get("date"):
                header += f"  ({entry['date']})"
            lines.append(header)
            if entry.get("subtitle"):
                lines.append(entry["subtitle"])
            if entry.get("link"):
                lines.append(entry["link"])
            for bullet in entry.get("bullets", []) or []:
                lines.append(f"- {bullet}")
            if entry.get("tools"):
                lines.append(f"Tools: {entry['tools']}")
            lines.append("")
        lines.append("")
    refs = content.get("references_list")
    if refs:
        lines.append("REFERENCES")
        lines.append("-" * 10)
        for r in refs:
            extra = " - ".join(x for x in [r.get("title"), r.get("contact")] if x)
            lines.append(f"{r.get('name','')}" + (f", {extra}" if extra else ""))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# PDF conversion / page count / font check
# ---------------------------------------------------------------------------

def convert_to_pdf(docx_path, out_dir):
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf", "--outdir", out_dir, docx_path],
        check=True, capture_output=True, timeout=120,
    )
    pdf_path = os.path.join(out_dir, os.path.splitext(os.path.basename(docx_path))[0] + ".pdf")
    if not os.path.isfile(pdf_path):
        raise RuntimeError("PDF conversion did not produce an output file.")
    return pdf_path


def count_pages(pdf_path):
    result = subprocess.run(["pdfinfo", pdf_path], check=True, capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", result.stdout, re.MULTILINE)
    return int(m.group(1)) if m else None


def check_fonts(pdf_path):
    """Returns (font_used_summary, warning_or_None). Confirms what
    actually rendered rather than trusting the requested font name --
    under LibreOffice, Calibri commonly substitutes to Carlito, which is
    metric-compatible but is worth knowing about, since a page-count
    check is only meaningful if the font that produced it is known."""
    result = subprocess.run(["pdffonts", pdf_path], check=True, capture_output=True, text=True)
    lines = [l for l in result.stdout.splitlines()[2:] if l.strip()]
    fonts_seen = set()
    for line in lines:
        parts = line.split()
        if parts:
            fonts_seen.add(parts[0])
    if not fonts_seen:
        return "unknown", "Could not determine the rendered font from the PDF."
    summary = ", ".join(sorted(fonts_seen))
    ok_names = {"Calibri", "Carlito"}
    if any(any(ok in f for ok in ok_names) for f in fonts_seen):
        if any("Carlito" in f for f in fonts_seen) and not any("Calibri" in f for f in fonts_seen):
            return summary, "Calibri substituted with Carlito (metric-compatible) -- expected under LibreOffice, not an error."
        return summary, None
    return summary, f"Expected Calibri/Carlito but the PDF reports: {summary}. Appearance may differ from what was intended."


# ---------------------------------------------------------------------------
# Keyword coverage (deterministic, single source of truth)
# ---------------------------------------------------------------------------

def _light_stem(word):
    w = word.lower()
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _tokens(text):
    return set(_light_stem(w) for w in re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]*", text.lower()))


def collect_draft_text(content):
    parts = [content.get("summary") or ""]
    for section in content.get("sections", []):
        for entry in section.get("entries", []):
            if "label" in entry and "values" in entry:
                parts.append(entry.get("label", ""))
                parts.append(entry.get("values", ""))
                continue
            parts.append(entry.get("title", ""))
            parts.append(entry.get("subtitle", "") or "")
            parts.append(entry.get("tools", "") or "")
            parts.extend(entry.get("bullets", []) or [])
    return " \n".join(parts)


def keyword_coverage(content):
    terms = content.get("posting_terms")
    if not terms:
        return None
    draft_text = collect_draft_text(content)
    draft_tokens = _tokens(draft_text)
    draft_lower = draft_text.lower()

    required_total = required_matched = 0
    preferred_total = preferred_matched = 0
    missing_required = []
    missing_preferred = []
    matched_required = []
    matched_preferred = []

    for t in terms:
        term = t.get("term", "")
        required = bool(t.get("required"))
        term_tokens = _tokens(term)
        # Literal phrase match OR every token of the term present somewhere
        # in the draft (handles multi-word terms without needing exact
        # phrase adjacency).
        matched = term.lower() in draft_lower or (term_tokens and term_tokens.issubset(draft_tokens))
        if required:
            required_total += 1
            if matched:
                required_matched += 1
                matched_required.append(term)
            else:
                missing_required.append(term)
        else:
            preferred_total += 1
            if matched:
                preferred_matched += 1
                matched_preferred.append(term)
            else:
                missing_preferred.append(term)

    # The matched_* lists name WHICH terms matched (not just how many), so the
    # draft preview can show the user their actual matches next to the gaps.
    return {
        "required_matched": required_matched,
        "required_total": required_total,
        "preferred_matched": preferred_matched,
        "preferred_total": preferred_total,
        "matched_required": matched_required,
        "matched_preferred": matched_preferred,
        "missing_required": missing_required,
        "missing_preferred": missing_preferred,
    }


# ---------------------------------------------------------------------------
# Claims-trace check (every number traces to a confirmed source)
# ---------------------------------------------------------------------------

NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?[xX]?")
# Trailing "x"/"X" is captured as part of the number so a sourced multiplier
# like "3x" is matched as one token "3x" (not split into "3" + a dangling
# "x") -- "3x growth" is a common, unambiguous idiom. source_numbers should
# then list "3x" to match, not "3". Deliberately NOT extended to k/m/b
# suffixes (4K, 3M, etc.) -- those collide too often with ordinary
# alphanumeric identifiers (model numbers, room numbers) to be worth it.


def claims_trace(content):
    issues = []
    for section in content.get("sections", []):
        for entry in section.get("entries", []):
            if "label" in entry and "values" in entry:
                continue
            source_numbers = entry.get("source_numbers")
            if source_numbers is None:
                continue  # no claim made about this entry's numbers -- skip, not a false positive
            allowed = set(source_numbers)
            text = " ".join([
                entry.get("title", ""),
                entry.get("subtitle", "") or "",
                entry.get("tools", "") or "",
                *(entry.get("bullets", []) or []),
            ])
            found = set(NUMBER_RE.findall(text))
            unverified = sorted(n for n in found if n not in allowed)
            if unverified:
                issues.append({
                    "entry": entry.get("title", "(untitled)"),
                    "unverified_numbers": unverified,
                })
    return issues


# ---------------------------------------------------------------------------
# Main build-and-fit loop
# ---------------------------------------------------------------------------

def collect_cut_first_candidates(content):
    out = []
    for section in content.get("sections", []):
        for entry in section.get("entries", []):
            if entry.get("tier") == "cut-first":
                title = entry.get("title") or entry.get("label") or "(untitled)"
                out.append(f"{section.get('heading','?')}: {title}")
    return out


def clean_stale(out_dir, stub):
    for pattern in (f"{stub}.pdf", f"{stub}-preview*.png", f"{stub}.docx", f"{stub}.txt"):
        for f in glob.glob(os.path.join(out_dir, pattern)):
            try:
                os.remove(f)
            except OSError:
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("content_json")
    parser.add_argument("output_base")
    parser.add_argument("--paper", choices=["A4", "Letter", "A4".lower(), "Letter".lower()], default=None)
    parser.add_argument("--body-size", type=float, default=10.5)
    parser.add_argument("--margin", type=float, default=0.65)
    parser.add_argument("--max-pages", type=int, default=1, choices=[1, 2, 3],
                         help="1 (default/ideal) -> 2 -> 3. Per the skill's CV length "
                              "policy, 3 is allowed only for a CV tailored to an actual "
                              "posting (posting_terms) or a fully general base CV "
                              "(cv_kind base_general) -- rejected outright otherwise.")
    parser.add_argument("--no-auto-fit", action="store_true")
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--filename-stub", default=None)
    args = parser.parse_args()

    result = {"status": "error"}

    if not os.path.isfile(args.content_json):
        print(json.dumps({"status": "error", "errors": [f"content file not found: {args.content_json}"]}, indent=2))
        sys.exit(1)

    try:
        with open(args.content_json, "r", encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "errors": [f"{args.content_json} is not valid JSON: {e}"]}, indent=2))
        sys.exit(1)

    errors = validate(content)
    if errors:
        print(json.dumps({"status": "error", "errors": errors}, indent=2))
        sys.exit(1)

    # Hard ceiling, not just a warning: a general base CV (no posting_terms,
    # i.e. nothing identifying this as tailored to an actual job posting)
    # must never reach 3 pages -- the skill's CV length policy states this
    # as an absolute, not a preference, so it's enforced here the same way
    # "never cut a protected entry" is enforced by collect_cut_first_candidates
    # only ever surfacing cut-first entries: structurally, not just by asking
    # nicely in the instructions.
    cv_kind = content.get("cv_kind")
    three_ok = (cv_kind == "base_general") or (bool(content.get("posting_terms")) and cv_kind != "base_role")
    if args.max_pages == 3 and not three_ok:
        print(json.dumps({
            "status": "error",
            "errors": [
                "--max-pages 3 was requested but this content isn't eligible for it "
                "(no \"posting_terms\" and no \"cv_kind\": \"base_general\", or "
                "\"cv_kind\" is \"base_role\"). Per the CV length policy, 3 pages is "
                "allowed only for a CV tailored to a real posting (include "
                "posting_terms) or a fully general base CV with no role in mind "
                "(set cv_kind to \"base_general\"). Otherwise use --max-pages 2."
            ],
        }, indent=2))
        sys.exit(1)

    out_dir = os.path.dirname(os.path.abspath(args.output_base)) or "."
    stub = args.filename_stub or os.path.basename(args.output_base)
    os.makedirs(out_dir, exist_ok=True)
    clean_stale(out_dir, stub)

    paper = infer_paper(content, args.paper.upper() if args.paper else None)
    paper_inferred = args.paper is None

    # The one free step-down lever is relative to whatever was REQUESTED,
    # never a fixed absolute -- a fixed (10.0, 0.6) target used to be
    # *larger* than a caller-supplied starting point smaller than that
    # (e.g. --body-size 9.5 --margin 0.5), so the "shrink" step could
    # silently grow the page back up instead of shrinking it further.
    # Clamped at a legibility/printability floor, and only added if it's
    # an actual reduction from the start on at least one axis.
    fallback_body = max(args.body_size - FIT_STEP_BODY_PT, FIT_MIN_BODY_PT)
    fallback_margin = max(args.margin - FIT_STEP_MARGIN_IN, FIT_MIN_MARGIN_IN)
    levers = [(args.body_size, args.margin)]
    if not args.no_auto_fit and (fallback_body < args.body_size or fallback_margin < args.margin):
        levers.append((fallback_body, fallback_margin))

    docx_path = os.path.abspath(args.output_base) + ".docx"
    pdf_dir = out_dir
    applied = None
    page_count = None
    date_warnings = []
    pdf_path = None

    try:
        for bsz, mgn in levers:
            date_warnings = build_docx(content, docx_path, Pt(bsz), Inches(mgn), paper)
            pdf_path = convert_to_pdf(docx_path, pdf_dir)
            page_count = count_pages(pdf_path)
            applied = {"body_size": bsz, "margin": mgn}
            if page_count is not None and page_count <= args.max_pages:
                break

        over_limit = page_count is not None and page_count > args.max_pages

        font_used, font_warning = check_fonts(pdf_path)

        if args.text:
            write_plain_text(content, os.path.abspath(args.output_base) + ".txt")

        kw = keyword_coverage(content)
        trace_issues = claims_trace(content)
    except BuildError as e:
        print(json.dumps({"status": "error", "errors": [str(e)]}, indent=2))
        sys.exit(1)
    except Exception as e:
        # Anything else (LibreOffice/poppler missing or failing, a
        # permissions error, etc.) still comes back as the script's own
        # one-JSON-result contract instead of an uncaught traceback.
        print(json.dumps({
            "status": "error",
            "errors": [f"Build failed ({e.__class__.__name__}): {e}"],
        }, indent=2))
        sys.exit(1)

    result = {
        "status": "over_length" if over_limit else "ok",
        "page_count": page_count,
        "max_pages": args.max_pages,
        "paper": paper,
        "paper_inferred": paper_inferred,
        "font_used": font_used,
        "font_warning": font_warning,
        "fit_applied": applied,
        "date_warnings": date_warnings,
        "keyword_coverage": kw,
        "claims_trace_issues": trace_issues,
        "files": {
            "docx": docx_path,
            "pdf": pdf_path,
            "txt": (os.path.abspath(args.output_base) + ".txt") if args.text else None,
        },
    }
    if over_limit:
        result["cut_first_candidates"] = collect_cut_first_candidates(content)
        result["note"] = (
            f"Still {page_count} pages after applying free font/margin fit levers "
            f"(target {args.max_pages}). Cut from cut-first entries above, or confirm "
            f"a longer document is acceptable -- this script does not choose content "
            f"to cut."
        )
    print(json.dumps(result, indent=2))
    sys.exit(0 if not over_limit else 2)


if __name__ == "__main__":
    main()
