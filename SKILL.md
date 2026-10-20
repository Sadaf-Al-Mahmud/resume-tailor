---
name: resume-tailor
description: Build, maintain, and tailor a professional CV/resume to a specific job posting (or as a strong general-purpose base CV). Use when the user asks to build, write, update, improve, review, or tailor a resume/CV/curriculum vitae to a role or job posting, for any country, industry, or career stage. Shows a draft for the user to confirm (what matches, what doesn't, what's included and left out, and why) before building the final ATS-safe, single-page-first .docx and PDF.
---

# Resume Tailor

Builds and tailors resumes/CVs from the user's real, verified experience. Works for any
country, any industry, any career stage — there is no single "home market" this skill is
tuned for. Every piece of localization (paper size, what a photo or personal details imply,
how much formality a summary line needs) is resolved per-user, per-request: by asking, or by
reading the job posting and the country the user names. Nothing here assumes one country's
norms as the default case.

## Core rules (apply throughout, not just at the step that mentions them)

1. **Never fabricate.** Every number, title, tool, and claim in the CV must come from
   something the user told you (directly, or already recorded in their resume bank — see
   below). If you can't trace a number to a source, don't write it; ask instead. `build.py`'s
   claims-trace check is a mechanical backstop for this, not a substitute for it — don't rely
   on the script to catch what you should never have written.
2. **Tiering protects the user's strongest material.** Every bank entry is tagged
   `protected`, `strong`, or `cut-first` (see Step 3). `protected` entries are never cut for
   length, never silently dropped, and never offered to the user as something to cut.
3. **Say what you left out, and why — always.** If something from the bank isn't going on
   this CV (wrong tier for the space available, not relevant to this posting, etc.), tell the
   user in the checkpoint message, in one line, why. If the user gave you a detail for this
   CV only and it was never added to their bank (see "CV-only information," Step 2), say so
   explicitly — don't let them believe it's saved when it isn't. If you try to save to the
   bank and the save fails, don't just fail silently: tell the user plainly that the save
   didn't go through, and show them the entry as plain text so they can keep a copy themselves.
4. **Gap-bridging has one hard boundary.** When a posting asks for something the bank doesn't
   obviously cover, you may rephrase genuine experience using the posting's vocabulary.
   Vocabulary may flex. Scope, seniority, and domain may never be stretched, implied, or
   reframed beyond what actually happened. See Step 5 and `references/bullet-writing.md` for
   the full rule and worked examples. Try it once, defensibly; if it doesn't hold up, flag the
   gap to the user instead of trying to force it — don't loop.
5. **Mechanical fit problems get mechanical fixes.** If a draft runs long, `build.py` already
   tries smaller font/margins automatically before anything else happens — that's free and
   lossless, so never manually shrink fonts or suggest it yourself. Only after that still
   isn't enough does content get cut, and only from `cut-first`-tier entries, and that
   decision is always the user's or yours to make deliberately — never the script's.
6. **No country is the default.** Don't assume paper size, photo norms, how much personal
   detail is normal, or anything else from one country's convention. Ask, or infer from the
   job posting and the country the user names, and say when you're inferring. And never
   present any specific country — including the user's own — as a pre-set choice in a
   multiple-choice question: let them type it (see Step 1).
7. **A photo, if used, is the user's real photo — never generate one.** If a photo belongs on
   the CV, only use an actual file the user supplied. Never create, generate, or describe an
   AI-made image standing in for the user's likeness.

## CV length policy

A CV's maximum acceptable length depends on what it's for, and it's never unlimited:

- **Base CV with a role/field in mind (no specific posting):** 1 page is the ideal and the
  starting target. 2 pages only if there's genuinely too much *relevant* material to fit in 1.
  **Never 3 pages for this kind of base CV.**
- **Fully general base CV (no role in mind, no posting):** its whole purpose is to hold
  everything the user has done, so 1 page is only the starting point, not a limiter — it may
  run to 2 or 3 pages. **But never silently:** before it goes past 1 page, the user is asked
  and agrees (see "Fully general base CV: ask before going past 1 page" below). Never past 3.
- **Tailored to a specific posting:** 1 page is still the ideal and the starting target. Go to
  2 pages only if needed. Go to 3 pages **only as a true last resort** — after filtering (see
  below) still doesn't bring it under 2, and only for someone with enough genuinely relevant
  experience (e.g., a more senior candidate) that cutting further would mean cutting things
  that actually matter for this posting. **Never go past 3 pages, ever.**

**Fully general base CV: ask before going past 1 page.** Don't filter this kind of CV for
length first — the user wants it complete. Instead:
1. Build at `--max-pages 1`. If it fits, done.
2. If `over_length`, rebuild the working draft at `--max-pages 2`, and at `--max-pages 3` only
   if 2 still doesn't fit (one step at a time; `build.py` only allows 3 here when the content
   has `"cv_kind": "base_general"`).
3. In the draft preview (Step 7), put this at the top of the open questions, in plain words:
   what they've added doesn't fit on one page, the full version runs N pages, and do they want
   to go beyond 1 page or not — and if not, offer to trim it back (naming the `cut-first`
   entries you'd drop first).
4. Their answer decides the page count. **No answer = not confirmed:** don't deliver the
   longer version on silence; ask again. If they choose to trim, filter as in the steps below,
   tell them what was cut and why, and rebuild at the lower count.

**How to decide for a tailored CV or a base CV with a role in mind — don't jump straight to
"allow more pages":**
1. Build at `--max-pages 1` first, always, regardless of how much material the bank has.
2. If `over_length`: before raising the page ceiling, filter. Go back through what you tiered
   `strong`/`protected` (Step 3) and judge each one specifically against what this CV is
   *for* — for a tailored CV, against the posting's actual stated requirements; for a base CV
   with a role/field in mind, against what generally matters for that kind of role; for a
   fully general base CV, against overall relevance/strength. Re-tier anything that doesn't
   clearly matter down to `cut-first` (or drop it), even if it's solid material — "good but not
   relevant to this" is exactly what gets filtered here. This is the same judgment Step 3
   already asks for, just explicitly applied *before* ever expanding the page count, not after.
3. Tell the user what got filtered and why, same as any other exclusion (Core rule 3) — one
   line each, in the checkpoint (Step 7). **If the user insists on keeping something you
   filtered out, include it** — this is their call to overrule, not a rule you enforce over
   their objection.
4. Rebuild at `--max-pages 1`. If it fits now, done.
5. Still `over_length` after genuine filtering (i.e., what's left really is necessary)? Escalate
   one step at a time — `--max-pages 2`, and, only for a tailored CV that still doesn't fit,
   `--max-pages 3` — never skip straight to the ceiling. Each escalation is a deliberate choice
   you make (or the user does), never a default.

`build.py` enforces the hard caps mechanically, not just by instruction: `--max-pages` only
accepts 1, 2, or 3, and it **refuses outright** (a clean `error` result, nothing built) if you
ask for 3 pages unless the content has `posting_terms` (tailored) or `"cv_kind":
"base_general"` (fully general base CV). A base CV with a role in mind (`"cv_kind":
"base_role"`) structurally cannot reach 3 pages through this script. The script can't know
whether the user agreed to extra pages — that part is on you (the ask above).

## Honest turn expectations

Tell the user up front (in your first reply) roughly how many turns this will take, so they
can plan around it:
- **Returning user with an existing bank:** usually 3-4 turns total (intake → draft preview
  → the user's decisions → final file).
- **New user, no bank yet:** usually 5-6 turns (intake → short interview to build the bank →
  draft preview → the user's decisions → final file), because a bank built from a real
  interview produces a far better CV than one guessed from a single paragraph.

The user always sees and approves a draft preview *before* the final file is built — that's
the turn that decides what goes in. If their changes are large — or a fully general base CV
needs a page-count decision they haven't made yet — expect one extra preview round. Don't promise a one-turn or two-turn CV — it isn't true, and overpromising just means
re-opening "finished" work later.

## Step 0 — Work out where the resume bank can live (silent, do this first)

The "resume bank" is the running record of the user's real experience (roles, projects,
education, skills, each with tier and `source_numbers`) that this CV — and every future one —
gets drafted from. Without a persisted bank, every session starts from zero, which wastes the
user's time and risks losing verified detail. Before Turn 1, silently check what's actually
available in this environment, in order of preference:

1. **A durable, cross-session memory/storage tool** (e.g., an `mcp__memory__*`-style tool, or
   an equivalent the environment exposes) — if present, this is where the bank lives. It
   survives across separate sessions.
2. **A persistent working-directory file** — if no durable memory tool exists but files
   written to the working directory are confirmed to persist across sessions in this
   environment, use a file (e.g., `resume-bank.md`) there instead.
3. **Neither** — if you can't confirm persistence either way, say so plainly the first time
   it matters (Step 2): tell the user this session can't guarantee the bank will still be
   here next time, and that you'll print the full bank in chat at the end so they can paste it
   into their own notes and bring it back next session (as pasted text, which you can parse
   back into a bank).

Don't guess silently and let the user discover data loss later — if you're in case 3, say so
before they invest time answering interview questions.

## Step 1 — Turn 1: one structured question

Ask a single message covering three things (use a multiple-choice/structured question tool if
available; otherwise ask plainly in text):

1. **Returning or new?** Do they already have a resume bank with you (check storage from Step
   0 first — if you find one, confirm it with them instead of asking blind), or is this the
   first time?
2. **What's the target?** One of:
   - A specific job posting (ask them to paste it or a link/description) — the **tailored**
     path: full fit verdict later, posting_terms extracted, length policy allows up to 3 pages
     as a last resort (see "CV length policy").
   - A **general base CV** — if so, ask the follow-up this implies: do they have a specific
     role or field in mind (so the CV is still weighted toward what usually matters for that
     kind of role, even with no literal posting to match against), or do they want a fully
     general CV with no particular role in mind at all? Either is fine — it only changes how
     Step 7's checkpoint is framed later, and it sets the page ceiling: a base CV aimed at a
     role/field stays within 2 pages, while a fully general one may run longer if the user
     agrees (see "CV length policy").
   - An update to an existing CV.
   This can all be one structured question with nested/follow-up options — it doesn't need to
   cost an extra turn.
3. **What country or place is this CV for?** Usually the country the employer is based in
   (for a remote job, the employer's country) — which can differ from where the user lives.
   It drives paper size (A4 vs. Letter) and is a prompt to flag any locale-specific
   conventions (e.g., whether a photo is expected, normal, unusual, or something to avoid for
   that market/employer type) — ask the user directly about these rather than assuming; if
   they don't know, say conventions vary by country and employer type and that you'll default
   to the safer, more universal choice (no photo, no birth date/marital status/nationality on
   the CV) unless they tell you otherwise.

   **How to ask it: let the user type it.** Never put a specific country in the fixed options
   of a multiple-choice question — not the user's own (even if you know it from memory or a
   profile), not a "common" one, not a region standing in for countries — because any place
   offered as a quick-pick tilts the skill toward that place, and where someone lives isn't
   necessarily where they're applying. Offer only non-country-specific choices (e.g., "No
   specific country / not sure yet") plus an **Other** option worded so it's clear they should
   type their country or place (and, if they're applying in several countries, the main one
   for this CV — one CV has one paper size) — or just ask it as a plain-text question. Only
   skip asking if the user already said the country themselves in this conversation.

   What goes into `target_country`:
   - Whatever they typed, as written — a bare country or "City, Country" both work.
   - If they typed only a city or a state/province, write it as "City, Country" when the
     country is unambiguous — `build.py` recognizes country names, not cities — and ask when
     it isn't (many place names exist in more than one country). Say in the preview that you
     inferred the country.
   - If they chose the no-specific-country option, leave it empty.

   Paper size is inferred from it; if it isn't a place `build.py` recognizes (or it's empty),
   it falls back to A4 — and the draft preview (Step 7) states the paper size so the user can
   correct it.

Don't ask these as three separate turns — one message, three questions, is the whole point of
the structured Turn 1.

## Step 2 — Load or build the bank

**Returning user with a confirmed bank:** load it. Skim for anything that looks stale (dates
that have clearly passed, a role they've likely left) and ask about it briefly rather than
assuming — one line, not a full re-interview.

**New user, or no bank found:** read `references/bank-build.md` now. It has the bank entry
format and a short, batched interview question set. Run the interview efficiently — batch
related questions together rather than one at a time, and stop asking once you have enough to
draft (don't chase exhaustive completeness on the first pass). After the interview, write the
bank to wherever Step 0 determined, and confirm to the user it's saved (or give the Step 0
case-3 fallback).

**CV-only information:** if, at any point, the user gives you a detail explicitly for this one
CV ("just for this one, don't save it") or gives something too thin/unverified to bank
confidently, use it for this CV but do **not** add it to the bank, and say so in the checkpoint
message (Core rule 3).

## Step 3 — Tier everything you're drawing on

Every entry used for this CV gets one tier:
- **`protected`** — the user's strongest, most relevant material for this target; never cut,
  always included if there's room for anything.
- **`strong`** — solid, relevant, include if space allows after protected entries.
- **`cut-first`** — weaker or less relevant to this specific target; the first candidates if
  the draft needs to shrink.

Tiering is a judgment call made against *this* target, not a fixed property of the bank entry —
the same entry can be `protected` for one CV and `cut-first` for another. Judge it against: the
posting's actual stated requirements (tailored path), what generally matters for the named
role/field (base CV with a role in mind), or overall relevance/strength (fully general base
CV). This same judgment gets re-applied, more strictly, as the first move if the draft runs
long — see "CV length policy" above.

## Step 4 — Mechanical thinness pre-filter

Before drafting bullets, scan the bank entries you plan to use for ones that are too thin to
write a real bullet from: no concrete outcome, no number, no tool/method named, just a vague
responsibility ("helped with marketing"). Don't silently turn these into polished-sounding but
empty bullets. Instead:
- If it's `cut-first` tier, it's fine to simply drop it or keep it minimal.
- If it's `strong` or `protected` tier (meaning it's actually important to include), this is
  exactly when gap-bridging (Step 5) or a quick clarifying question is worth it — a thin entry
  in an important slot is a drafting problem to solve now, not something to paper over with
  vague corporate language.

## Step 5 — Draft

Read `references/bullet-writing.md` before writing bullets — it has the full phrasing rules
(outcome-first structure, truthfulness, team-credit attribution, skills-need-evidence, jargon/
audience translation) and worked examples. In particular:

- **Gap-bridging** (Core rule 4): when the posting uses language the bank doesn't, check
  whether a real `strong`/`protected` entry can be honestly described using that language.
  Never gap-bridge from `cut-first` entries — if the bank's only answer to a requirement is
  weak, that's a genuine gap to flag, not something to dress up. Try once; if it's not
  defensible, say so to the user plainly in the checkpoint rather than forcing it.
- **Team-credit:** if an outcome was a group effort, say so — attribute honestly ("as part of
  a team of 4," "co-led with...") rather than writing an individual-sounding verb for shared
  work.
- **Skills need evidence:** don't list a skill in a Skills section unless at least one bullet
  or project elsewhere on the CV (or the bank) actually demonstrates it being used.
- **Jargon check:** if a bullet uses internal/niche jargon the reader of this specific CV
  (a recruiter, a hiring manager in a different function) likely won't recognize, translate it
  to plain, specific language — keep the precision, drop the insider shorthand.

Assemble the draft into the `content.json` shape `scripts/build.py` expects (full schema in
the script's module docstring — read it with `python3 scripts/build.py --help` or by opening
the file if you need the exact fields). Set `tier` and, for any entry with a number in it,
`source_numbers` on every entry — this is what makes Core rule 1 and the claims-trace check
actually work. Set `target_country` to the country/place the user typed (Step 1), and
`posting_terms` (each term marked `required` or not) when there's an actual posting. Set
`cv_kind` to `tailored` (a posting), `base_role` (base CV with a role/field in mind) or
`base_general` (base CV, no role in mind) — it's what lets `build.py` apply the right page cap.

## Step 6 — Build a working draft (internal — nothing is delivered yet)

This build exists to get real numbers (page count, keyword match, claims-trace) for the draft
preview in Step 7 — **the user doesn't receive the file yet.** Build into a scratch/working
folder, not into whatever location the user's downloads or outputs surface automatically, so
nothing reaches them before they've approved the draft. The file is delivered only in Step 10.

Run, starting with the default (1-page) target every time — see "CV length policy" for the
full escalation ladder (`--max-pages 1` → filter → `--max-pages 2` → `--max-pages 3`, never
skipping a step, never exceeding the cap for the CV type; a fully general base CV skips the
filtering and instead gets the user's go-ahead before it goes past 1 page):
```
python3 scripts/build.py <content.json> <output_base>
```
Pass `--paper A4` or `--paper Letter` only if you need to override the automatic inference;
otherwise let it infer from `target_country` (A4 is the default for anything not explicitly a
Letter-paper market — see the script's `LETTER_COUNTRIES` comment for what that short,
non-exhaustive list is and why). Don't pass `--body-size`/`--margin` yourself — the automatic
fit-down lever already starts from the sensible default and shrinks it for you.

Read the single JSON result it prints:
- `status`: `ok` or `over_length` (still too long after the automatic font/margin levers) or
  `error` (fix the listed validation errors and rerun).
- `page_count` / `fit_applied`: what actually happened; if `fit_applied` differs from your
  requested size, the script already shrank it for you — don't do that manually too.
- `date_warnings`: any date it had to approximate (e.g., a season turned into an approximate
  month) — mention these to the user if any look wrong.
- `keyword_coverage` (only present if you supplied `posting_terms`): the deterministic
  required/preferred keyword match against the posting — counts, plus the actual lists
  `matched_required`, `matched_preferred`, `missing_required`, `missing_preferred`. Use these
  lists, not your own impression, for the matches and non-matches you show the user in Step 7.
- `claims_trace_issues`: any number in the draft that doesn't trace to that entry's
  `source_numbers`. Resolve every one before showing the draft preview — either it's a real
  source you forgot to list (add it to `source_numbers`) or it's a number that shouldn't be
  there (fix the text). Never show or deliver a CV with unresolved claims-trace issues.
- If `status` is `over_length`: don't just reach for a higher `--max-pages`. First filter per
  "CV length policy" above, then rebuild at the same `--max-pages`. Only escalate the page
  ceiling, one step at a time, after genuine filtering still doesn't fit — and the result's
  `cut_first_candidates` is there to inform that filtering, never to be cut from automatically.
  Don't shrink fonts/margins further yourself — the script already tried the lossless option.
- If it's still `over_length` at the highest cap this CV type allows (2 pages for a base CV
  with a role in mind, 3 for a tailored one or a fully general base CV), stop — don't build past the cap, and don't cut `protected` material
  yourself. Take the closest working build to the preview (Step 7), say plainly that it's over
  the cap, and let the user decide what to condense or drop; honor their choice.
- If you request `--max-pages 3` on content that isn't eligible (no `posting_terms`, and not
  `cv_kind: base_general`; or `cv_kind: base_role`), the script refuses outright (`status:
  error`) rather than building — this should never happen if you follow the escalation ladder
  above and set `cv_kind` correctly.

## Step 7 — The draft preview (the one consolidated checkpoint)

(This is Turn 2 for a returning user with a bank already in hand; one turn later, after the
interview, for a new user — either way, it's a single consolidated message, not several.)

**This is a text-only preview. Do not attach, send, or save the `.docx`/`.pdf` anywhere the
user would see it at this step.** Its job is to let the user decide what goes into the CV
*before* anything is final — what matched, what didn't, what you chose to include or leave
out and why — using the real results of the Step 6 working build. The file comes only after
they've reviewed this and confirmed (Step 10).

Write it as one scannable message (short lines, not paragraphs), in this order:

1. **Verdict, appropriate to what this CV is for:**
   - **Tailored to a posting:** a blunt fit verdict — strong fit / conditional fit / weak fit —
     based on the keyword match and how much gap-bridging was needed. Don't hedge this into
     mush; the user needs the honest read to decide whether applying is worth their time.
   - **Base CV with a role/field in mind:** a lighter version of the same honesty, without a
     keyword score to point to — e.g., "this is a strong general CV for [field]; it leans
     hardest on X and Y, and would need [Z] added if you end up targeting a role heavy on Z."
   - **Fully general base CV:** no fit verdict (there's nothing to measure fit against) — just
     an honest completeness/quality read, e.g., "this gives a solid, complete picture of your
     background" or "this leans thin in [area] — worth building out before you use it."
2. **Keyword match** *(tailored path only — for a base CV, say in a few words that there's no
   posting to match against and move on)*:
   - **Matches:** the terms in `matched_required` and `matched_preferred`.
   - **Doesn't match:** the terms in `missing_required` and `missing_preferred`. For each,
     one phrase on *why*: a genuine gap (nothing in their background supports it), or it *is*
     in the bank but you left it off this draft (name the entry — they may want it back).
   Take both lists from the script's result, not from impression.
3. **Included, and why** — every entry/section going on the CV, with a one-line reason (e.g.,
   "protected — directly shows the SQL requirement"). Entries sharing a reason can be grouped.
   Also say here, one line each, anything that's for this CV only and was not saved to the
   bank (Step 2), and any bank save that failed (Core rule 3).
4. **Left out, and why** — every notable exclusion, with a one-line reason (Core rule 3),
   including anything filtered for length per "CV length policy" (say so even if the user
   never asked — that's still an exclusion they didn't make themselves) and anything the
   thinness filter in Step 4 dropped.
5. **Gap-bridged wording** — flag every bullet where you rephrased real experience into the
   posting's vocabulary, so the user can confirm it's accurate or correct it.
6. **The draft itself** — the summary line and each section's entries and bullets, as plain
   text, as they will read on the CV. This is what lets the user judge the actual wording, not
   just the decisions behind it.
7. **Format** — paper size (and that it was inferred from the place they gave — plus the
   country you took it to be, if they typed only a city — so they can correct it), the page
   count from the working build (and, if above 1, why — what was
   filtered and what remains; for a fully general base CV, that it's over 1 page because
   everything was kept, pointing to the question in item 8), and any `date_warnings`.
8. **Open questions** — a thin entry you couldn't resolve, a date you're unsure about, a tier
   judgment call. List them explicitly. For a fully general base CV that didn't fit on one
   page, the page-count question goes first ("CV length policy": your experience doesn't fit
   on 1 page, the full version is N pages — go beyond 1 page, or trim?).

End by handing the decisions to the user plainly: they can add back anything left out, drop
anything included, reword or correct anything — or reply that it looks good and you'll build
the final file.

If the user's reply doesn't address one of the listed open items, treat that item as **not
confirmed** — don't assume silence means agreement, especially for a gap-bridged claim. Ask
again or leave it out, don't ship it on an assumption.

## Step 8 — Apply the user's decisions

Take the user's reply to the draft preview and apply it:
- **Add back** something you left out or filtered → include it. This is the user's call to
  overrule, not a rule you enforce over their objection. It still has to be real (Core rule 1)
  — from the bank or from what they tell you now. If it pushes the CV past its current page
  count, follow the "CV length policy" ladder (one step at a time, never past the cap for this
  CV type; for a fully general base CV, that means asking before going past 1 page, as in the
  preview) and tell them.
- **Drop** something included → drop it.
- **Reword or correct** → apply it, and update `source_numbers` if any number changed.
- **Open questions** → apply their answers. Any item they didn't answer stays unconfirmed:
  leave it out, or ask once more — don't assume.
- **New information** they give you here follows the Step 2 rules (add it to the bank unless
  they said it's for this CV only).

Then rebuild with the same Step 6 command, so the working files match their decisions, and
resolve any new claims-trace issues. If they confirmed the preview with no changes, no rebuild
is needed — the Step 6 build is the final candidate.

Don't re-run the whole preview for small, clearly specified edits — apply them and mention
what changed when you deliver. Two exceptions, where a short check-in comes first:
- Your changes introduced **new wording the user hasn't seen** (anything gap-bridged, or
  wording you wrote for something they added) → show just that wording and get a yes.
- The changes are big enough to **move the fit verdict or keyword match meaningfully** → give
  a short updated version of Step 7 items 1–2 rather than leaving them with a stale verdict.

## Step 9 — Final QA pass before delivering

Before the final delivery, re-read the actual rendered output (open the PDF/preview, don't just
trust the JSON result) with a reader's eye:
- Does it read cleanly top to bottom in under 10 seconds for the overall shape (name, target,
  strongest point) to land?
- Any leftover placeholder text, double spacing, or awkward line break from the build?
- Every claims-trace issue resolved, every open item from the preview resolved or explicitly
  still open and disclosed?
- Does the file/page actually match what the latest build's JSON result said (right paper
  size, right page count)?
- Does it contain exactly what the user decided in Step 8 — nothing added or removed that
  they didn't decide?

## Step 10 — Deliver

This is the first and only point the user receives a file. Send the final `.docx` (the
editable, ATS-safe primary deliverable) — copy it out of the scratch folder to wherever
deliverables go, or rebuild directly into that location. Mention the PDF only if the user wants
a preview copy or needs to submit a PDF specifically — don't produce files the user didn't ask
for. Close with one honest next step if there's a real one (e.g., "want me to tailor this same
bank to a second posting?") — don't manufacture one if there isn't.

## Reference files

- `references/bank-build.md` — bank entry format and the new-user interview question set.
  Read only when Step 2 needs it (no existing bank).
- `references/bullet-writing.md` — bullet-writing rules, gap-bridging and team-credit detail,
  worked examples. Read before Step 5.
- `references/ats-rules.md` — the ATS-safety rules the `.docx` structure is built to satisfy,
  and how `build.py`'s automatic fit levers work. Read if the user asks why the CV is
  formatted a certain way, or if something about ATS compatibility needs explaining.
