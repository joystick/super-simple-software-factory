---
type: Skill
title: grill-with-docs
description: One-line composition of grilling + domain-modeling; SSSF's bootstrap entry point.
tags: [pocock, interview, bootstrap, sssf]
resource: downloads/skills/skills/engineering/grill-with-docs/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# grill-with-docs

**Intent:** a relentless interview that leaves durable artifacts behind —
"Run a `/grilling` session, using the `/domain-modeling` skill." The entire
skill body is that one line; everything else is the two composed skills'
behavior.

**Snapshot state:** identical in both snapshots (8 lines,
`disable-model-invocation: true` — human-only entry).

**SSSF relevance:** the entry point of Part C ("going dark"): a human runs
`/grill-with-docs`, the session writes `CONTEXT.md`/`docs/adr/`, the human
commits, and only then does the headless queue run. SSSF deliberately
**excludes** it from `skill_engineering/` vendoring: it is pure interactive
composition, and its `disable-model-invocation: true` marks it human-only.
The handoff from a finished grill session to `/triage` (filing the ticket)
is **manual and unenforced** — prior audit finding 3.1.3 [MEDIUM]. Nothing
in the fresh clone closes that gap either: `loop-me` is another interview
entry (not a bridge), and `to-spec`/`to-tickets` still require the human to
type them.

**Headless verdict:** never headless; it exists precisely to front-load the
human interaction so the rest can be.
