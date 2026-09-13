---
type: Skill
title: triage
description: The state machine that gates work into ready-for-agent; drifted between the two snapshots.
tags: [pocock, triage, queue, sssf, drift]
resource: downloads/skills/skills/engineering/triage/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# triage

**Intent:** move issues through a state machine of triage roles —
`needs-triage` → `needs-info` / `ready-for-agent` / `ready-for-human` /
`wontfix` — categorising, verifying, grilling when needed, and writing
durable **agent briefs** (bundled `AGENT-BRIEF.md`) plus an
`.out-of-scope/` knowledge base (`OUT-OF-SCOPE.md`).

**Snapshot drift (verified by diff, substantive):**

- Fresh adds `disable-model-invocation: true` — triage became human-only
  entry upstream; the local copy is model-invokable.
- Fresh extends the machine to **external PRs** ("a PR is an issue with
  attached code"), with `[PR]`/`[issue]` tagging in discovery and
  PR-specific readings of `ready-for-agent`/`ready-for-human`.
- Local body references `grill-with-docs`; fresh reroutes to `grilling` +
  `domain-modeling` directly.

**SSSF relevance:** `ready-for-agent` is the **contract state** between the
two systems: `/triage` (interactive, human judgment on feasibility/
compliance/security) posts the durable agent brief and flips the label;
`adw_watch.py` only ever claims already-`ready-for-agent` tickets and then
writes its own `claimed`/`resolved` states. Label strings come from
`docs/agents/triage-labels.md`, written by
[setup-matt-pocock-skills](/pocock-skills/skills/setup-matt-pocock-skills.md).

**Headless verdict:** deliberately interactive — the judgment steps are the
point. SSSF's design keeps it that way and automates only what happens
after `ready-for-agent`.
