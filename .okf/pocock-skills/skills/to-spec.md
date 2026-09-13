---
type: Skill
title: to-spec
description: Current upstream successor of write-a-prd/to-prd - conversation to published spec, explicitly without an interview.
tags: [pocock, spec, engineering, rename]
resource: downloads/skills/skills/engineering/to-spec/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# to-spec

**Intent:** "Turn the current conversation into a spec and publish it to
the project issue tracker: **no interview, just synthesis** of what you've
already discussed." Lands in `.scratch/<feature-slug>/spec.md` on the local
tracker — **and applies the `ready-for-agent` triage label itself**
("no need for additional triage"), corrected from an earlier draft of this
concept that said `needs-triage` — verified directly against the SKILL.md
text on 2026-09-13. Its own "sketch the seams, check with the user" step
stands in for a triage gate in its model.

**Lineage (verified):** `write-a-prd` (gen 1: interview → PRD → GitHub
issue; still installed locally AND vendored into SSSF downstream repos) →
`to-prd` (gen 2: synthesis → configured tracker; also still installed
locally) → `to-spec` (gen 3: PRD vocabulary dropped repo-wide in 1.2.0).
The interview half was deliberately moved out into `grilling`/`wayfinder`.

**Snapshot state:** fresh clone only (76 lines,
`disable-model-invocation: true`). Not installed locally.

**SSSF relevance:** this is the skill SSSF's playbook *means* when it says
`/write-a-prd`. Ironically, gen 3 already solves the exact problem SSSF's
planner prompt patches by hand ("write-a-prd: never prompt — the request is
already in `prompt` below"): `to-spec` never prompts by design. Re-vendoring
`to-spec` in place of `write-a-prd.md` would simplify the planner overrides
— but the planner prompt and playbook key on the old name, so the swap must
be coordinated (see `plans/pocock-protocol-sssf-integration.md`).

**Headless verdict:** headless-safe by design on the interview question —
the most headless-friendly spec skill of the three generations. But its
`ready-for-agent` auto-apply (above) is unsafe for SSSF's queue specifically:
`/triage` judges feasibility/compatibility/compliance/security, a fuller
check than this skill's own approval step — a headless override must force
`Status: needs-triage` instead, or this skill silently disables SSSF's
triage gate. Fixed in `planner/system.md`'s composed-skills override (R2,
`plans/pocock-protocol-sssf-integration.md`).
