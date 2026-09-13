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
already discussed." Lands in the configured tracker in `needs-triage`
state; on the local tracker that is `.scratch/<feature-slug>/spec.md`.

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

**Headless verdict:** headless-safe by design — the most headless-friendly
spec skill of the three generations.
