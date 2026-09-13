---
type: Skill
title: setup-matt-pocock-skills
description: One-time repo configuration that writes the tracker doc, triage labels, and domain-doc layout — the literal seam between Pocock skills and SSSF.
tags: [pocock, setup, issue-tracker, sssf, seam]
resource: downloads/skills/skills/engineering/setup-matt-pocock-skills/SKILL.md
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
---

# setup-matt-pocock-skills

**Intent:** configure a repo once for the engineering skills: pick the
**issue tracker** (GitHub / GitLab / local markdown / freeform "other"),
confirm the **triage label** strings for the five canonical roles, choose
the **domain docs** layout (single-context `CONTEXT.md` + `docs/adr/` by
default), then write it all down and register an `## Agent skills` section
in `CLAUDE.md`/`AGENTS.md`.

**What it writes:** `docs/agents/issue-tracker.md` (from the bundled
`issue-tracker-{github,gitlab,local}.md` templates),
`docs/agents/triage-labels.md`, `docs/agents/domain.md`. Every other
engineering skill (`to-spec`, `to-tickets`, `triage`, `code-review`,
`wayfinder`) resolves the tracker through these files rather than hardcoding
paths.

**The local-markdown template** (identical shape in both snapshots) defines
the convention SSSF's `adw_watch.py` reads: `.scratch/<feature-slug>/spec.md`
+ one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`,
`Status:` line for triage state, `Blocked by: NN, NN`, `## Comments` at the
bottom, and a "Wayfinding operations" section (map/frontier/claim/resolve).

**Snapshot drift:** none that matters — the diff across all six files is
punctuation (local uses em-dashes, fresh uses colons) plus equivalent
rewording. Same sections, same defaults, same file targets.

**SSSF relevance:** the downstream repo's `docs/agents/issue-tracker.md`
was **re-synced 2026-09-09 to this skill's canonical local template**, then
extended with SSSF queue semantics (`claimed`/`resolved` states written by
`adw_watch.py`, `Type:` lines, per-feature-scoped blocking). It is the one
file both systems read; whoever owns it owns the contract.

**Headless verdict:** interview-driven, human-only entry
(`disable-model-invocation: true` in both snapshots). Run once, by a human.
