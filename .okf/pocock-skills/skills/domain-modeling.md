---
type: Skill
title: domain-modeling
description: Builds and sharpens a project's domain model; writes CONTEXT.md and ADRs.
tags: [pocock, domain, engineering]
resource: downloads/skills/skills/engineering/domain-modeling/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# domain-modeling

**Intent:** keep the project's vocabulary and decisions durable — build the
domain model while discussing terminology, and record it as `CONTEXT.md`
(glossary/model) and `docs/adr/*` (decisions), per its bundled
`CONTEXT-FORMAT.md` and `ADR-FORMAT.md`.

**Snapshot state:** byte-identical in both snapshots (75 lines,
model-invoked).

**SSSF relevance:** produces the exact artifacts SSSF's headless planner is
told to treat as **binding vocabulary** (`CONTEXT.md`, ADRs read from the
working tree). The bootstrap chain is: grilling asks, domain-modeling
writes, git commit makes it visible to the queue — the commit step is
prescribed by the playbook but enforced by nothing (prior audit, Diagram A).

**Headless verdict:** conversational by design, but the *writing* half is
mechanical; safe headless when the decisions are already settled (e.g. the
documenter stage updating CONTEXT.md after a shipped slice).
