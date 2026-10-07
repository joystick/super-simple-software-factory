---
title: Skill compatibility checklist
---

# Skill compatibility checklist

SSSF is a **skill-agnostic factory**: a role (`scout`, `planner`, `builder`,
`reviewer`, `documenter`) is a prompt seam — `system.md` + `user.md` plus a
typed output contract — with no opinion about *how* the work inside that
seam gets done. `skill_engineering:` is the plug for a **method** into that
seam, resolved entirely in the adopting repo's own `sssf.config.yaml`. The
factory itself never assumes, defaults to, or ships pre-wired with any
specific third-party skill (Pocock's, Trail of Bits', or anyone else's) —
see [`Ignored-field-warnings.md`](Ignored-field-warnings.md) and
`docs/manual-skill-engineering.md` for the mechanism this checklist governs.

**The problem this page exists to solve:** no third-party skill was written
with SSSF's headless, single-envelope, two-channel-output conveyor in mind.
Composing one onto a role's prompt (`skill_engineering.compose()`) delivers
its real, full text verbatim — but "the text is real" is not the same claim
as "the text's own assumptions hold in this role, headless." Every item
below is a real, independently-verified case where that gap mattered, not a
theoretical concern.

## Before vendoring any skill onto any role, check all six

### 1. Dispatch dependency

Does the skill's own text invoke another skill — "Call the Skill tool for
X", `$skill-name`, or similar meta-dispatch — rather than containing its
substance directly?

**Verified case:** `wayfinder/SKILL.md`'s own step 1 is "Call the Skill
tool twice, for 'grilling' and 'domain-modeling'." Composed alone (as in a
real, live `sssf.config.yaml` checked for this page), neither sibling file
is vendored — not composed into the prompt, not reachable via the Skill
tool either, since a headless `claude -p --system-prompt` run also carries
`--setting-sources ''`, which hides the operator's installed
`~/.claude/skills/` from the node. `grill-with-docs/SKILL.md` is the
extreme version: it is *only* a one-line dispatcher ("Call the Skill tool
twice, for 'grilling' and 'domain-modeling'") with no substance of its own
— vendoring it alone, for any role, composes nothing useful.

**Rule:** if a skill dispatches to a sibling, either vendor the sibling
alongside it (same `skill_engineering:` list, composition order matters —
see #5) or don't vendor this skill onto a headless role at all.

### 2. Interactive fallback

Does the skill contain an "ask the user" / "if unspecified, ask" / "if
nothing is found, ask" instruction?

**Verified case:** `code-review/SKILL.md` has two: "pin the fixed point...
if they didn't specify one, ask for it" and "if nothing is found, ask the
user where the spec is." The reviewer role's own `user.md` happens to
supply an equivalent for the second (reads `plan.md` from
`context_handoff_dir`, falls back to `prompt`) — but this was never
verified end to end before being cited in the playbook as settled, and the
first fallback (the fixed point) is not addressed by anything in the
role's prompt at all.

**Rule:** for every interactive fallback a skill has, trace the specific
role's `system.md`/`user.md` and prove — don't assume — that the fallback
is unreachable in that role's real flow. If you can't prove it, don't
vendor the skill onto that role headless, or supply the missing input
explicitly in the role's own prompt first.

### 3. Output shape

Does the skill assume a specific issue tracker, file convention, or
artifact shape that may not match this repo's actual configuration?

**Example:** a skill that calls `gh issue create` directly assumes a
GitHub-backed tracker; vendoring it onto a role in a repo using the
local-markdown convention (`docs/agents/issue-tracker.md` saying "Local
Markdown") produces a skill trying to shell out to a tracker that isn't
the one this repo actually uses.

**Rule:** check the skill's own process section for tracker/file-shape
assumptions against this repo's real `docs/agents/issue-tracker.md` (or
equivalent) before vendoring, not after something fails.

### 4. Writes and permissions

Does the skill assume write access to a path the role's `writes:`/
`defaults.protected_files` would actually block?

**Rule:** cross-check the skill's process section for every path it
expects to create or edit against the role's real `writes:` entry in
`sssf.config.yaml`. A skill that assumes it can write CI secrets or commit
messages onto a role configured `writes: []` (read-only — see
[`Permissions-and-writes.md`](../quality-gates-and-permissions/Permissions-and-writes.md))
will have its writes silently rolled back after the fact, not blocked
loudly at the point of the attempt.

### 5. Composition order

Does the skill assume another skill already ran earlier in the same
prompt (e.g. a planning methodology that assumes a spec already exists)?

**Rule:** `skill_engineering.compose()` appends in the exact order listed
in the roster entry's `skill_engineering:` array — never sorted,
deliberately, since sorting would silently change behaviour and an
unstable order would break prompt caching. Order the list to match the
skills' own internal assumptions about sequence (e.g. `wayfinder` before
`to-spec` before `to-tickets`, matching the order those skills name
themselves in), and record *why* in a comment if the order isn't obvious
from the names alone.

### 6. Terminology and convention drift

Does the skill reference a filename or vocabulary term that must match
what this repo's own templates (`scout/system.md`, `planner/system.md`,
etc.) and other already-vendored skills actually look for?

**Verified case:** Pocock's skills renamed their domain-doc convention from
`CONTEXT.md`/`CONTEXT-MAP.md` to `GLOSSARY.md`/`GLOSSARY-MAP.md` in v1.3.0.
SSSF's own shipped `scout`/`planner` templates still look for `CONTEXT.md`
as of this writing. Vendoring the new version of `domain-modeling` or
`grill-with-docs` onto a role today, without also updating that role's own
prompt or the adopting repo's convention, produces a scout that never finds
the glossary and a planner that never reads it — silently, not loudly.

**Rule:** before vendoring a new or updated version of any skill, diff its
current content against the hash your `skills-lock.json`/provenance header
last recorded, and check its own changelog for renamed
files/fields/conventions. Update every file in this repo that references
the old name in the same change, not as a follow-up.

## What "passing" this checklist looks like

Every vendored skill in `adws/adw_data/skill_engineering/` should have a
one-line note, next to its entry in `sssf.config.yaml` or in a nearby
comment, recording which of the six checks were actually traced (not
assumed) for that role — the same discipline `writes: []` and
`protected_files` already apply to permissions, applied here to behavioral
compatibility.

## See also

- [`docs/manual-skill-engineering.md`](../../manual-skill-engineering.md) —
  the full `skill_engineering` mechanism this checklist governs.
- [`Ignored-field-warnings.md`](Ignored-field-warnings.md) — the one
  compatibility check SSSF already enforces mechanically (whether a
  `coding_agent` honours `skill_engineering` at all); everything above is
  the behavioral layer that mechanism can't check for you.
- [`Defaults-merging.md`](Defaults-merging.md) — how a role inherits or
  overrides its `skill_engineering:` list from `defaults`.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-10-07 | Initial checklist, derived from three real, independently-verified compatibility gaps found while tracing the actual prompt-composition mechanics against a live `sssf.config.yaml`: `wayfinder`'s unvendored Skill-tool dispatch, `code-review`'s unaddressed interactive fallback, and the `CONTEXT.md`→`GLOSSARY.md` rename drift. |
