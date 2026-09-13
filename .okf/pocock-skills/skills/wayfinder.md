---
type: Skill
title: wayfinder
description: Plans oversized work as a map of decision tickets on the issue tracker; SSSF's queue borrows its mechanics.
tags: [pocock, planning, queue, sssf]
resource: downloads/skills/skills/engineering/wayfinder/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# wayfinder

**Intent:** plan a chunk of work too big for one agent session as a shared
**map** of decision tickets on the issue tracker, resolved one at a time
until the way is clear — then hand off to `/to-spec` (upstream's own
CHANGELOG names that merge point).

**Mechanism:** map + child tickets; each ticket typed
`research`/`prototype`/`grilling`/`task` and classified **HITL** (human in
the loop) or **AFK** (agent alone); **frontier** = first open, unblocked,
unclaimed ticket; **claim** by assignment; **resolve** appends the answer
and updates the map. Renamed from `decision-mapping` in 1.1.0.

**Snapshot state:** byte-identical in both snapshots (129 lines,
`disable-model-invocation: true`). Note both copies reference `research`
and `prototype`, which are NOT installed locally — the local copy names
collaborators it cannot reach.

**SSSF relevance:** SSSF's Part D queue (`adw_watch.py`, `just sssf`)
**reuses wayfinder's map/child/frontier/claim/resolve mechanics as the
queue** rather than inventing new ones — the downstream
`docs/agents/issue-tracker.md` extends the "Wayfinding operations" section
with `claimed`/`resolved` states that `adw_watch.py` itself writes. It is
also vendored (provenance header, 2026-09-09) into the planner's prompt,
with the planner instructed: "if it finds no fog, do not stop and ask" and
to skip its filing behavior when the prompt is an already-filed ticket.

**Headless verdict:** the mechanics (frontier/claim/resolve) are fully
headless-safe — SSSF proves it; the mapping conversation itself is HITL.
