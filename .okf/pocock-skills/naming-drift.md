---
type: Analysis
title: Naming drift across Pocock skill generations
description: >-
  Verified rename chains between the locally installed skill generation and
  the current upstream, and the exact impact on SSSF's playbook and vendored
  skill_engineering files.
tags: [pocock, drift, renames, sssf, vendoring]
generated:
  by: claude-fable-5/20260912
  at: 2026-09-12
status: stable
sources:
  - id: changelog
    resource: downloads/skills/CHANGELOG.md
    title: mattpocock-skills CHANGELOG
  - id: vendored-files
    resource: a downstream project/adws/adw_data/skill_engineering/
    title: Vendored skill files in a real SSSF downstream repo (provenance headers read 2026-09-12)
  - id: playbook
    resource: docs/playbook-adopting-sssf.md
    title: SSSF adoption playbook v4.5
  - id: planner-system
    resource: .claude/skills/sssf/templates/prompt_engineering/planner/system.md
    title: SSSF planner system prompt template
---

# Naming drift across Pocock skill generations

Three generations of the "conversation → spec → tickets" skills exist on
this machine simultaneously. The chains, verified against the upstream
CHANGELOG and file diffs:[^changelog]

## The rename chains

| Generation 1 (oldest, GitHub-only) | Generation 2 (tracker-agnostic, "PRD" era) | Generation 3 (current upstream, "spec" era) |
|---|---|---|
| `write-a-prd` (interview → PRD → GitHub issue) | `to-prd` (synthesis → PRD → configured tracker) | `to-spec` (synthesis → spec → configured tracker; **explicitly no interview**) |
| `prd-to-issues` (PRD → GitHub issues) | `to-issues` (spec → configured tracker) | `to-tickets` (one file per ticket locally; native blocking edges on GitHub/GitLab) |
| `review` | `code-review` | `code-review` (PRD language dropped in 1.2.0) |
| `decision-mapping` | — | `wayfinder` (renamed in 1.1.0) |
| — | — | `implement` / `implement-spec` (new: execute the spec/tickets) |

Evidence: CHANGELOG 1.1.0 introduces `to-spec`/`to-tickets` and routes
ask-matt's main flow `idea → /to-spec → /to-tickets → /implement`; 1.2.0
"skills-to-prd [is] a dead slug for the renamed skill; it now links
`to-spec`", drops every remaining "PRD" mention, and renames nothing back.
The local install (`~/.claude/skills/`) holds generations 1 AND 2 **side by
side** (`write-a-prd` + `to-prd`, `prd-to-issues` + `to-issues`, `review` +
`code-review`) with generation-3 copies of everything else — it is a
transitional snapshot, not one coherent release.[^changelog]

**The semantic shift matters more than the names:** `write-a-prd` conducts a
*user interview*; `to-spec` is "no interview, just synthesis of what you've
already discussed" — upstream moved the interview entirely into
`grilling`/`wayfinder`. That is exactly the property SSSF's playbook Part C
("the interview `write-a-prd` wants doesn't have anyone to answer it")
works around by hand today.

## `prd-to-plan` is an SSSF-side invention/carry-over

The vendored file `adws/adw_data/skill_engineering/prd-to-plan.md` in the
downstream repo (a downstream project) has **no `sssf:vendored` provenance header**
— unlike its four siblings — and `prd-to-plan` exists in neither snapshot of
the upstream collection. It is a hand-authored (or pre-vendoring-era) skill
text: "Turn a PRD into a multi-phase implementation plan … saved as a local
Markdown file in ./plans/". Its closest upstream successors are `to-tickets`
(slicing, but into tracker tickets rather than a local plan file) and
`implement`/`implement-spec` (execution). `vendor_skill.py` would refuse to
overwrite it, by design.[^vendored-files]

## Where the old names are load-bearing in SSSF

- `docs/playbook-adopting-sssf.md` — the bootstrap chain is written as
  `/grill-with-docs → /write-a-prd → /prd-to-plan` throughout (lines ~149,
  162, 256, 283, 471-547, 617-777 and the version history).[^playbook]
- `.claude/skills/sssf/templates/prompt_engineering/planner/system.md` — the
  planner's headless-composition section is titled "On the skills composed
  below (wayfinder, write-a-prd, prd-to-plan, tdd)" and gives per-skill
  no-prompt overrides under those names.[^planner-system]
- Downstream `adws/adw_data/skill_engineering/` — files named
  `write-a-prd.md`, `prd-to-plan.md`, `wayfinder.md`, `tdd.md`,
  `code-review.md`. Four of five carry provenance headers pointing at
  `~/.agents/skills/<name>/SKILL.md` (a third snapshot, vendored
  2026-09-09).[^vendored-files]

Consequence: anyone who installs the **current** upstream (plugin or
skills.sh) gets no `write-a-prd` and no `prd-to-plan` to vendor; re-vendoring
under the new names (`to-spec.md`) silently breaks the planner prompt's
per-skill override sections, which key on the old names. The full impact
analysis and recommendations live in
`plans/pocock-protocol-sssf-integration.md`.

[^changelog]: `downloads/skills/CHANGELOG.md`, entries 1.0.0-1.2.3.
[^vendored-files]: Provenance headers read from `a downstream project/adws/adw_data/skill_engineering/*.md`, 2026-09-12.
[^playbook]: `docs/playbook-adopting-sssf.md` (v4.5), grep verified 2026-09-12.
[^planner-system]: `.claude/skills/sssf/templates/prompt_engineering/planner/system.md:32-51`.
