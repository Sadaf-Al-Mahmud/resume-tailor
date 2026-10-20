# Bullet-writing rules

Read this before drafting any entry's bullets (SKILL.md Step 5). These rules apply to every
entry regardless of country, industry, or career stage — none of them are market-specific.

## 1. Truthfulness is absolute

Never write a number, outcome, tool, or claim that doesn't trace back to something the user
told you (directly, or already recorded in their bank). If you're unsure whether a detail is
accurate, ask — don't round up, don't infer a plausible-sounding number, don't borrow a
metric from a similar-sounding example. Every entry you draft with a number in it needs that
number listed in `source_numbers`, so `build.py`'s claims-trace check can verify it. If a
number genuinely has no clean source (the user said "a lot" or "significantly"), either ask
for the real figure or write the sentence without a fabricated number — "significantly" is
weaker than a real number, but it's honest, and honest-but-modest beats impressive-but-false
every time.

## 2. Outcome-first structure (XYZ-style)

Prefer: **what you did** + **how/with what** + **what resulted**, in that order, outcome
leading or closing depending on which is stronger:

> "Built a [thing], using [method/tool], resulting in [outcome]."

or, outcome-first when the outcome is the strongest part:

> "[Outcome], by building a [thing] using [method/tool]."

A bullet with no real outcome is a responsibility, not an achievement — it's acceptable
(especially for early-career entries where not every line will have a metric), but it should
never be dressed up with adjectives to sound like it has an outcome it doesn't have. A plain,
honest responsibility statement beats an inflated one.

**Weak (adjective-padded, no real content):**
> "Successfully leveraged various tools to drive impactful results in a dynamic environment."

**Strong (concrete, specific, honestly scoped):**
> "Built a dashboard connecting [data source] to [tool], configuring N charts with filters for
> [dimensions]; used it to brief stakeholders on weekly trends."

## 3. Team-credit attribution

If an outcome was produced by a group and the user wasn't solely responsible for it, say so.
Don't write a bullet in a way that implies solo credit for group work — this is both dishonest
and easy for an interviewer to catch out in two follow-up questions.

**Risky (implies solo credit for what was actually a team outcome):**
> "Increased event attendance by 40% through a new marketing strategy."

**Honest (same achievement, properly attributed, still strong):**
> "Co-led a 3-person team that redesigned the event's marketing approach, contributing to a 40%
> attendance increase; personally owned the [specific piece the user actually did]."

If the user's specific contribution within the group is identifiable (they owned one
deliverable, one workstream), name that explicitly — a bullet can honestly credit a team
outcome while still being specific about the individual's own piece.

## 4. Skills need evidence

Don't list a skill (in a Skills-style entry, or anywhere else) unless it's actually
demonstrated somewhere on the CV or in the bank — a bullet, a project, a course. A list of
unsupported skill names reads as padding to anyone reviewing the CV, including automated
screening that cross-checks skills against the rest of the document. If a skill is real but
not yet demonstrated anywhere else on this CV, either add a demonstrating bullet if there's
room, or leave the skill off this version.

## 5. Gap-bridging: the defensibility rule

When a job posting uses a term or asks for an experience the bank doesn't obviously contain,
check whether a real `strong` or `protected` entry can be honestly described using the
posting's own vocabulary. This is legitimate — most people undersell what they did using
different words than a given posting uses — but it has one hard boundary:

- **Vocabulary may flex.** If the user did something that's genuinely the same activity under
  a different name, use the posting's term. "Maintained a shared tracker used by the team"
  and a posting that asks for "stakeholder reporting" may be the same real activity described
  two ways — if it's true, say it in the posting's language.
- **Scope, seniority, and domain may never be stretched.** Don't imply the user led something
  they contributed to, owned something they assisted with, worked at a level above what they
  actually held, or worked in a domain they didn't actually touch. If the honest version of an
  entry simply isn't what the posting is asking for, that's a real gap — flag it to the user in
  the checkpoint message rather than writing around it.

**Example — legitimate gap-bridge:**
Posting asks for "cross-functional collaboration." The bank entry says: "Worked with the
design and engineering sub-teams on a class project to align the dashboard's requirements
before building it." That genuinely is cross-functional collaboration — rephrasing it using
the posting's term is honest.

**Example — NOT a legitimate gap-bridge (don't do this):**
Posting asks for "led a team of 5+." The bank entry says the user was one of 4 members on a
project with no formal lead. Writing "Led a team of 5" or even "Led a cross-functional
initiative" is not supported by what happened — this is scope/seniority inflation, not
vocabulary flexing. The honest move is to flag this as a gap in the checkpoint message (e.g.,
"this posting wants team-lead experience; nothing in your bank currently shows that — want to
mention it anyway and be ready to discuss honestly in an interview, or skip emphasizing this
requirement?") rather than writing a bullet that won't survive a follow-up question.

**Try once, don't loop.** Attempt a defensible rephrase a single time. If it doesn't hold up
under the boundary above, stop trying to force that requirement to fit — flag it as a gap and
move on. Don't keep generating alternate phrasings hoping one slips past the rule; the rule
isn't a wording problem to work around.

## 6. Jargon and audience translation

Internal shorthand, company-specific tool names, or niche technical jargon that the reader of
*this* CV won't recognize should be translated to plain, specific language — without losing
precision. The right level of plainness depends on who's reading: a CV going to a generalist
recruiter needs more translation than one going to a specialist on the hiring team; infer this
from the posting and the role, and when genuinely unsure, lean toward the plainer version.

**Before:** "Owned the QBR deck and drove alignment via the RACI."
**After:** "Prepared the quarterly business review presentation and clarified team
responsibilities using a standard accountability framework."

Keep technical terms that the role genuinely requires and that a reader in that field would
expect (e.g., naming the actual tools/languages/methods used) — translation means dropping
insider shorthand and unexplained acronyms, not dumbing down legitimate technical content.
