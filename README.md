# resume-tailor

A Claude Skill for building, maintaining, and tailoring a professional CV/resume to a specific
job posting — or as a strong general-purpose base CV. Works for any country, industry, or
career stage; nothing in it assumes a single "home market."

## What it does

- Maintains a growing, reusable **resume bank** of the user's real experience (education,
  roles, projects, skills), so every future CV is drafted from verified material instead of
  starting over.
- Tailors a CV to a specific job posting: deterministic keyword-coverage checking, honest
  gap-bridging (vocabulary may flex to match the posting's language; scope/seniority/domain
  never do), and a blunt fit verdict (strong/conditional/weak) instead of generic encouragement.
- **Never builds the final file blind.** Before anything is delivered, the user gets a
  text-only draft preview: which keywords matched and which didn't (and why), what was
  included and why, what was left out and why, any gap-bridged wording, and the draft text
  itself. The user adds back, drops, or corrects whatever they want; only then is the final
  `.docx`/PDF built and delivered.
- Builds a clean, ATS-safe, single-column `.docx` (and PDF) — real list styles, real
  right-aligned tab stops computed from the actual page size/margins, a real heading style, a
  standard widely-installed font, correct paper size (A4 or Letter) inferred from the target
  country.
- Enforces a **claims-trace** check: every number that ends up in the drafted text must trace
  back to a number the user actually stated for that entry, or it's flagged.
- Applies free, lossless page-fit levers (smaller font/margins) automatically before ever
  suggesting content be cut — and when content does need to be cut, only from entries tagged
  `cut-first`; entries tagged `protected` are never cut or silently dropped.
- Enforces a **CV length policy**: 1 page is always the starting target. A base CV aimed at a
  role/field never exceeds 2 pages. A fully general base CV (no role in mind) is meant to hold
  everything, so it may run to 2 or 3 pages — but only after the skill asks the user and they
  agree. A CV tailored to an actual posting may reach 3 pages only as a deliberate last resort,
  after filtering content against the posting's real requirements. `build.py` only accepts
  `--max-pages 1|2|3` and refuses a 3-page request unless the content has `posting_terms` or
  `"cv_kind": "base_general"` (a clean error, not a built document). Full procedure in
  `SKILL.md`'s "CV length policy" section.

## Structure

```
resume-tailor/
├── SKILL.md                      # Main instructions Claude reads first
├── scripts/
│   └── build.py                  # Validate -> build .docx -> PDF -> page/font/keyword/
│                                  # claims-trace checks, one JSON result
└── references/
    ├── bank-build.md             # Bank format + new-user interview questions
    ├── bullet-writing.md         # Bullet-writing, gap-bridging, team-credit, jargon rules
    └── ats-rules.md              # ATS-safety rules + the fit-level pipeline
```

`README.md` (this file) is for the source repository only — it isn't needed at runtime and is
excluded from the packaged `.skill` file.

## How to install

**Option 1: Claude app (claude.ai or desktop)**
1. Go to the Releases section of this repo and download `resume-tailor.skill`.
2. In Claude, open Settings, then Capabilities, then Skills.
3. Upload the downloaded file. (If your screen only accepts a .zip, rename the file's ending from .skill to .zip.)
4. Start a new chat and say: "Help me tailor my CV to this job posting."

**Option 2: Claude Code**
1. Download or clone this repo.
2. Copy the `resume-tailor` folder into `~/.claude/skills/`.
3. Restart Claude Code and ask it to build or tailor your CV.

**What it needs to build files:** Python 3 with `python-docx`, LibreOffice and poppler-utils. Claude's own environment normally has these.

## Requirements

`scripts/build.py` needs:
- Python 3 with `python-docx` installed (`pip install python-docx`)
- LibreOffice (`soffice`) on PATH, for `.docx` -> PDF conversion
- `poppler-utils` (`pdfinfo`, `pdffonts`) on PATH, for the page-count and font-verification
  checks

These are the same tools most sandboxed Claude environments already provide; if a tool is
missing, the error from `build.py` will say which step failed.

## Using it standalone

`scripts/build.py` is a normal command-line tool and can be run outside of Claude too:

```
python3 scripts/build.py content.json out/resume
```

See the module docstring at the top of `scripts/build.py` for the full content JSON schema and
all CLI options.

## Design notes

- **No single country is assumed anywhere.** The user types their country or place (no
  country is ever offered as a pre-set choice). Paper size is inferred from that free text
  against the primary-Letter countries/territories in Unicode CLDR's paper-size data, and
  defaults to A4 (the ISO 216 standard most of the world uses) otherwise; the result always
  reports whether the size was inferred, and the draft preview states it so the user can
  correct it. Photo and personal-detail conventions are never assumed from one market —
  `SKILL.md` asks the user or infers from the posting instead.
- **Tab-stop alignment is computed at build time** from the document's actual page width and
  margins, not a hardcoded constant — a fixed value is only correct for one specific
  paper-size/margin combination and silently overhangs the margin for any other.
- **Content decisions stay with the assistant/user, never the script.** `build.py` will tell
  you a document is over length and which `cut-first`-tier entries exist, but it never chooses
  what to cut itself.
- **Every build-time failure comes back as the same one JSON result**, success or error (a bad
  `photo_path`, a missing LibreOffice/poppler install, anything else) — never an uncaught
  traceback, so a caller never has to special-case how the script fails.
- **The auto-fit step-down is always relative to whatever was requested**, never a fixed
  absolute target — so a caller starting from already-tight custom `--body-size`/`--margin`
  values gets a genuinely smaller fallback, not one that's accidentally larger than what it
  started from.

## License / sharing

Built to be published and used by anyone, for any CV. No personal or organization-specific
content is embedded anywhere in the skill.
