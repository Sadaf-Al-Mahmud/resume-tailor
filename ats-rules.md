# ATS-safety rules and the fit-level pipeline

Read this if you need to explain why the CV is structured a certain way, or before deviating
from the default structure `scripts/build.py` produces. These rules are about how an
Applicant Tracking System and a human skimmer both parse a document — they apply everywhere,
regardless of country or industry.

## Why the structure is what it is

- **Single column, no tables.** Multi-column layouts and tables are read in an unpredictable
  order (sometimes left-to-right across columns, sometimes top-to-bottom within one column
  first) by many ATS parsers, which can silently scramble dates, titles, and bullets in the
  system a recruiter actually searches. `build.py` never produces a table or a column layout.
- **Real list styles, not typed bullet characters.** A bullet typed as a literal "•" or "-"
  character is just a character to a parser; a real list-style paragraph (what `build.py`
  uses, via Word's "List Bullet" style) is recognized as a list item. Never hand-type bullet
  characters into a title or body run.
- **Standard section headings.** Use conventional headings ("Experience," "Education,"
  "Skills," "Projects," not creative renamings like "My Journey") so both ATS keyword parsing
  and a human skimmer recognize the section instantly.
- **Real tab-stop alignment for dates, not spaces.** A right-aligned date needs an actual tab
  stop, computed from the real page width and margins — not a run of manually-typed spaces,
  which breaks alignment the moment the font or margin changes. `build.py`'s
  `right_tab_position()` computes this fresh from the document's actual page width and
  margins at build time, specifically because a fixed/hardcoded tab position is only correct
  for one exact paper-size-and-margin combination and silently overhangs the margin for any
  other (confirmed during development: a fixed 7.2in stop was correct for Letter at 0.65in
  margins and wrong for A4 or for a tightened margin).
- **Standard, widely-installed fonts.** `build.py` uses Calibri (or its open-source
  metric-compatible substitute, Carlito, under LibreOffice rendering) — a font available
  everywhere, not a decorative or unusual typeface an ATS or a different machine might not
  render consistently.
- **A real heading style, not just bold text.** `build.py` defines an actual paragraph style
  ("CVSectionHeading," based on Word's built-in Heading 2) for section headings, so a parser
  that keys off document structure — not just bold formatting — still recognizes the section
  breaks.

## Text-extraction details (found by a real copy-paste test)

Pasting a generated PDF into Notepad exposed two issues, both fixed in `build.py` and covered by
regression checks:

- **Bullets are a plain "•" in the body font.** The template's default bullet is a Symbol-font
  private-use glyph (U+F0B7), which shows up as a stray odd character in copied text. The bullets
  are still real list items — only the glyph changed.
- **Two spaces precede every right-aligned date.** Some PDF viewers copy the gap of a right tab
  as nothing, gluing the date to the end of the title ("Management" + "Expected 2027"). The real
  spaces keep them apart. The tab stop still does the alignment.

One known limit: some extractors (for example poppler's default `pdftotext` mode) may still list
a right-aligned date on its own line. Others (`pdftotext -raw`, `pypdf`) keep it beside the title.
No layout trick fully removes this without giving up the right-aligned date, so it is accepted.

## Paper size

There's no single global default. `build.py` infers A4 vs. Letter from `target_country`: a
short, explicitly non-exhaustive allowlist of Letter-paper markets (see `LETTER_COUNTRIES` in
the script) maps to Letter; everything else — which is most of the world — defaults to A4. The
build result flags whether the size was inferred or explicitly requested, specifically so an
ambiguous or unrecognized country isn't silently guessed without a note. If the user names a
country not on the Letter list, or doesn't know, A4 is the safer default, but always check the
build result's `paper`/`paper_inferred` fields and mention them if there's any doubt.

The match is on country names (plus common spellings and abbreviations), not on cities or
states — so a bare city or state name in `target_country` falls back to A4 even when its country
is a Letter market. That's why SKILL.md Step 1 has the assistant write a bare city as "City,
Country" when the country is unambiguous. Anything still unrecognized lands on A4, and the draft
preview states the paper size so the user can correct it (or `--paper` can force it).

## The fit pipeline: mechanical first, content cuts second, never the other way around

This is about *how* a too-long draft gets shorter. For *how many pages are allowed in the
first place* (1 page ideal, when 2 is acceptable, when — rarely — 3 is), see SKILL.md's "CV
length policy" section; that's the single source of truth for page-count ceilings, not
repeated here to avoid the two drifting out of sync.

There is no contradiction between "never manually shrink fonts" and "shrink before cutting
content," because those apply to different actors:

1. **`build.py` tries its own automatic, lossless step-down first.** When a draft comes out
   longer than the target page count, the script automatically retries once with a smaller
   body size and tighter margins (its one built-in fit lever) before reporting anything back.
   This is free — no content is lost, nothing about the CV's substance changes.
2. **The assistant/user never manually shrinks fonts or margins.** Don't suggest "let's just
   make the font smaller" as a fix you perform by hand — that's exactly what step 1 already
   tries automatically. Manually micromanaging font size outside the script risks producing a
   document that looks inconsistent or that strays from the tested, ATS-safe defaults.
3. **Only if the result is still `over_length` after that does content get cut** — and only
   from `cut-first`-tier entries (see SKILL.md Step 3), and that choice is always made
   deliberately by the assistant or the user, never by the script. `build.py` reports
   `cut_first_candidates` precisely so this decision is informed, not guessed.

## Keep-with-next and widow/orphan control

Titles, subtitles, and the first bullet of a multi-bullet entry are set to stay with the
content that follows them (`keep_with_next`), so a page break never lands between an entry's
title and its own first line of detail. This is handled automatically by `build.py` — it's
mentioned here only so you know not to manually insert page breaks or extra blank paragraphs
to work around a bad break; if a break looks wrong, it's a signal to check the actual page
count/fit result, not to hand-patch the document.
