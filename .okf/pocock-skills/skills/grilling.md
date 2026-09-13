---
type: Skill
title: grilling
description: The relentless-interview primitive that most other Pocock skills compose.
tags: [pocock, interview, productivity]
resource: downloads/skills/skills/productivity/grilling/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# grilling

**Intent:** stress-test a plan, decision, or idea by interviewing the user
relentlessly — walk the design tree branch by branch until every leaf is a
concrete decision; explore the codebase instead of asking when a question is
answerable from code.

**Snapshot state:** byte-identical in both snapshots (29 lines,
model-invoked). The collection's most-composed primitive: `grill-me`,
`grill-with-docs`, `loop-me`, `triage`, `wayfinder`,
`improve-codebase-architecture`, and the `writing-*` skills all invoke it.

**SSSF relevance:** this is the interactive half SSSF deliberately does NOT
vendor. A grilling session needs a human answering; SSSF's bootstrap (Part
C) runs it via [/pocock-skills/skills/grill-with-docs.md](/pocock-skills/skills/grill-with-docs.md)
before the headless loop starts, so the loop never needs to prompt live.

**Headless verdict:** protocol is meaningless without a human respondent.
Never attach to an unattended agent.
