---
type: Skill
title: code-review
description: Two-axis review (Standards, Spec) since a fixed point; headless-safe, vendored by SSSF.
tags: [pocock, review, engineering, sssf]
resource: downloads/skills/skills/engineering/code-review/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# code-review

**Intent:** review the changes since a fixed point (commit, branch, tag, or
merge-base) along two axes — **Standards** (repo's documented coding
standards) and **Spec** (does the code match the originating issue/spec) —
run as two parallel sub-agents, reported side by side. If no spec is found
it asks the user where it is; the Spec axis skips when there is none.

**Snapshot state:** byte-identical in both snapshots (88 lines,
model-invoked). 1.2.0 renamed its vocabulary from issue/PRD to issue/spec.
The local install ALSO retains the older `review` variant side by side —
two skills answering the same trigger phrases.

**SSSF relevance:** vendored (provenance header, `~/.agents/skills/...`,
2026-09-09) into `adws/adw_data/skill_engineering/code-review.md` — the
protocol text rides on an SSSF agent's system prompt as its review method.
Its "ask the user where the spec is" branch is one of the interactive
fallbacks SSSF's planner prompt explicitly overrides for headless runs.

**Headless verdict:** headless-safe (read-only analysis) once the
ask-the-user fallback is overridden, which SSSF does.
