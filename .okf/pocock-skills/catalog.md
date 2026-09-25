---
type: Skill Collection
title: Matt Pocock's Skills For Real Engineers
description: >-
  What the Pocock skill collection is, its two install philosophies, and the
  two on-disk snapshots this bundle compares (fresh upstream clone vs. the
  locally installed set), including their verified drift.
tags: [pocock, claude-code, skills, sssf]
resource: https://github.com/mattpocock/skills
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
stale_after: 2026-12-12
sources:
  - id: fresh-clone
    resource: downloads/skills/
    title: Fresh git clone of mattpocock/skills (audited 2026-09-12)
  - id: local-install
    resource: ~/.claude/skills/
    title: Locally installed skill set (older, mixed-generation snapshot)
  - id: upstream-changelog
    resource: downloads/skills/CHANGELOG.md
    title: mattpocock-skills CHANGELOG (v1.0.0-1.2.3)
  - id: adr-0002
    resource: downloads/skills/.agents/adr/0002-ship-as-a-claude-code-plugin.md
    title: ADR 0002 - ship as a Claude Code plugin
  - id: invocation-doc
    resource: downloads/skills/.agents/invocation.md
    title: .agents/invocation.md - model-invoked vs user-invoked
---

# Skills For Real Engineers

A collection of small, composable Claude Code / Codex skills by Matt Pocock
for "real engineering — not vibe coding": requirements interviewing, spec
writing, ticket slicing, domain modeling, TDD, code review, issue triage.
Explicitly positioned against process-owning frameworks (GSD, BMAD,
Spec-Kit): each skill is short, hackable, and composes with the others
rather than owning the whole pipeline.[^fresh-clone]

## Two install philosophies

The README names them explicitly — "Two ways in, two philosophies. Pick one:
installing both leaves you with every skill twice":[^fresh-clone]

1. **Claude Code plugin (subscribe-only)** — `claude plugins install
   mattpocock-skills`. A managed, read-only bundle that auto-updates when
   upstream ships. Only the *promoted* buckets (`engineering/`,
   `productivity/`) are exposed; `misc/`, `in-progress/`, `deprecated/` are
   not.[^adr-0002]
2. **skills.sh (copy-and-hack)** — `npx skills@latest add mattpocock/skills`.
   Copies editable skill files into your project/agent; you own them, nothing
   updates behind your back, `npx skills update` pulls upstream when you
   choose. This is the "for tinkerers" path and the only path for Codex today
   (a native Codex plugin is deferred because Codex's manifest cannot select
   two bucket folders and drops symlinks on install).[^adr-0002]

Every skill carries an invocation policy: **user-invoked** skills set
`disable-model-invocation: true` (only a human typing the slash command can
fire them; no other skill can reach them) while **model-invoked** skills are
reachable by model or human. Cross-skill dependencies are expressed as "Call
the Skill tool with \"grilling\"" instructions, not file paths.[^invocation-doc]

## The two snapshots compared here

| | Fresh clone | Local install |
|---|---|---|
| Location | `downloads/skills/skills/` (this repo) | `~/.claude/skills/` |
| Vintage | current upstream (CHANGELOG through 1.2.3) | mixed: many files byte-identical to fresh, but retains a **pre-rename generation** of the spec/ticket skills |
| Skill count | 37 `SKILL.md` (18 engineering, 8 in-progress, 4 misc, 7 productivity, 0 deprecated) | 23 top-level skills, of which 5 are not Pocock skills at all (`okf`, `validate`, `visualize`, `find-skills`, `ubiquitous-language`) |
| Unique to it | `to-spec`, `to-tickets`, `implement`, `implement-spec`, `codebase-design`, `diagnosing-bugs`, `prototype`, `research`, `resolving-merge-conflicts`, `wizard`, `ask-matt`, all in-progress/misc skills | `write-a-prd`, `to-prd`, `to-issues`, `prd-to-issues`, `review` (all superseded upstream — see [naming drift](/pocock-skills/naming-drift.md)) plus the 5 non-Pocock skills |

Key structural facts verified by diff:

- `setup-matt-pocock-skills` exists in **both** snapshots with the same six
  files (`SKILL.md`, `domain.md`, `triage-labels.md`,
  `issue-tracker-{github,gitlab,local}.md`); the diff is **punctuation only**
  (em-dashes → colons) plus one substantive line: fresh drops the local
  tracker's `map.md` phrasing tweak. Functionally identical.
- `issue-tracker-local.md` describes the **same file shape in both
  snapshots**: `.scratch/<feature-slug>/spec.md` + one file per ticket at
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, `Status:` line for triage
  state, `## Comments` at the bottom. SSSF's `adw_watch.py` was built against
  this shape and it has **not** changed upstream.
- `triage` **has** drifted: the fresh version adds
  `disable-model-invocation: true`, extends the state machine to external
  PRs ("a PR is an issue with attached code"), and reroutes its grilling
  dependency from `grill-with-docs` (local) to `grilling` +
  `domain-modeling` directly (fresh).
- A **third snapshot** exists on this machine and matters for provenance:
  `~/.agents/skills/` — the path stamped into SSSF's vendored files'
  provenance headers (`source: ~/.agents/skills/<name>/SKILL.md`,
  vendored 2026-09-09). Not audited file-by-file here.

See [skill-matrix.md](/pocock-skills/skill-matrix.md) for the complete
per-skill table and [naming-drift.md](/pocock-skills/naming-drift.md) for the
rename chains.

[^fresh-clone]: `downloads/skills/README.md`, read in full 2026-09-12.
[^adr-0002]: `downloads/skills/.agents/adr/0002-ship-as-a-claude-code-plugin.md`.
[^invocation-doc]: `downloads/skills/.agents/invocation.md`.
