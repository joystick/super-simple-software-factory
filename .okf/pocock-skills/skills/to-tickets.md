---
type: Skill
title: to-tickets
description: Current upstream successor of prd-to-issues/to-issues - spec to tracer-bullet tickets with blocking edges; nearest living relative of SSSF's prd-to-plan.
tags: [pocock, tickets, engineering, rename]
resource: downloads/skills/skills/engineering/to-tickets/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# to-tickets

**Intent:** break a plan, spec, or the current conversation into
**tracer-bullet vertical-slice tickets**, each declaring its blocking
edges, published to the configured tracker — native issue dependencies on
GitHub/GitLab, or one file per ticket at
`.scratch/<feature>/issues/<NN>-<slug>.md` locally (never a single combined
tickets file — a 1.2.x hardening).

**Lineage (verified):** `prd-to-issues` (gen 1, GitHub-only; installed
locally) → `to-issues` (gen 2, tracker-agnostic; installed locally) →
`to-tickets` (gen 3). CHANGELOG 1.1.0 routes the main flow `idea → /to-spec
→ /to-tickets → /implement`.

**Relation to SSSF's `prd-to-plan`:** `prd-to-plan` (hand-authored in SSSF
downstream repos, in **neither** upstream snapshot) slices a PRD into a
multi-phase plan saved as ONE local file in `./plans/`. `to-tickets` is the
same slicing intent with a different output contract: many tracker tickets
with blocking edges — which is exactly the shape SSSF's Part D queue needs
(the playbook itself flags "prd-to-plan phases need their own issue files
with `Blocked by:` to be queue-pickable"). `to-tickets` closes natively the
gap `prd-to-plan` leaves.

**Snapshot state:** fresh clone only (106 lines,
`disable-model-invocation: true`). Not installed locally.

**Headless verdict:** headless-plausible — pure synthesis and file/tracker
writes; no interview in the protocol.
