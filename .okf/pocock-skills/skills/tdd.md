---
type: Skill
title: tdd
description: Red-green-refactor protocol; headless-safe and vendored onto SSSF agents.
tags: [pocock, tdd, engineering, sssf]
resource: downloads/skills/skills/engineering/tdd/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# tdd

**Intent:** build features and fix bugs test-first — the red → green loop,
with bundled `tests.md` and `mocking.md` references and a lean on
`codebase-design` for interface guidance (its inline deep-modules notes were
removed in 1.0.0 in favour of the shared skill).

**Snapshot state:** byte-identical in both snapshots (39 lines,
model-invoked).

**SSSF relevance:** the canonical example of a **headless-safe engineering
discipline** attached via `skill_engineering:` — `vendor_skill.py` copies
the SKILL.md body (provenance-stamped) into
`adws/adw_data/skill_engineering/tdd.md` and SSSF appends it to the
planner's system prompt. Vendored in the downstream repo from
`~/.agents/skills/tdd/SKILL.md` on 2026-09-09. Note the vendored text still
references calling `codebase-design` via the Skill tool — a skill the
headless agent may not have; in practice the protocol degrades gracefully.

**Headless verdict:** fully headless-safe; it is a discipline, not a
conversation.
