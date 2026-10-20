# Building a resume bank (new user, or no existing bank found)

Read this only when SKILL.md Step 2 determines there's no existing bank to load. A returning
user with a confirmed bank should skip this entirely — don't re-run an interview on someone
who already has one.

## What the bank is for

The bank is the durable, growing source of truth for a person's real experience — every
future CV (for any posting, in any tailoring direction) gets drafted from it, rather than from
scratch each time. A thorough first interview pays off across every CV built afterward, which
is why it's worth a real (if efficient) conversation rather than a single rushed paragraph.

## Bank entry format

Store each entry with these fields — this maps directly onto what `scripts/build.py` consumes
for a normal (non-skills-style) entry, plus the tier/source-number fields the skill itself
uses:

```
- section: (e.g., "Education", "Experience", "Projects", "Certifications")
  title: short headline (e.g., "BBA, Supply Chain Management" / "Marketing Intern")
  subtitle: organization/institution (optional)
  date: as the user stated it (normalize later, don't lose the original)
  link: a URL if relevant (optional — a repo, a portfolio piece, a published artifact)
  tools: comma-separated tools/methods used (optional)
  bullets: a list of real, specific outcomes or responsibilities
  source_numbers: every number that appears anywhere in this entry's bullets/title/tools,
                   listed here as the verified source of truth for that number
  default_tier: protected | strong | cut-first — the user's own sense of how important this
                is overall (this is a starting point; actual tier is re-judged per target CV
                in SKILL.md Step 3, but a sensible default saves re-asking every time)
```

For a Skills-style entry (a simple label + comma-separated list), store just:
```
- section: "Skills"
  label: (e.g., "Data & Analytics")
  values: comma-separated list
```
— remembering Core rule / bullet-writing rule 4: don't bank (or later include) a skill that
isn't demonstrated somewhere else in the bank.

## Running the interview efficiently

Don't ask one question at a time with a full turn each — batch related questions together.
A reasonable shape:

**Batch 1 — the skeleton (one message):**
- What's your current (or most recent) education — degree, institution, dates (or expected
  dates)?
- What roles, internships, or significant projects do you want to draw on? Just list them by
  name/title for now — details come next.
- Any certifications, publications, or notable external recognition worth including?

**Batch 2 — depth, per item named above (can be one message per item, or grouped if the user
prefers to go fast):**
For each role/project: what did you actually do, what tools/methods did you use, and what was
the real outcome — with a real number if there is one (don't let the user guess a number; if
they're not sure, ask them to check rather than estimate, or mark it without a number)? Was
this solo or a team effort, and if a team, what was your specific piece?

**Batch 3 — skills and extras (one message):**
- What skills/tools do you want listed, and where (which bullet/project above) does each one
  actually show up? (Enforces bullet-writing rule 4 at collection time, not just at drafting
  time.)
- Anything else — languages, volunteer work, relevant coursework — worth having in the bank
  even if it won't appear on every CV?

Stop once there's enough to draft a solid CV — the bank doesn't need to be exhaustively
complete on the first pass; it can grow over future sessions as the user adds more. If the
user is clearly in a hurry, say so plainly: a shorter interview now means a thinner bank and
more gap-bridging/clarifying questions later, and let them choose.

## After the interview

Write the bank to wherever SKILL.md Step 0 determined (durable memory tool, persistent file,
or neither). Confirm what was saved. If Step 0 landed on "neither" (no confirmed persistence),
print the full bank as plain text at the end of the session so the user has something to paste
back in next time — don't let them walk away thinking it's saved when you can't confirm that.
