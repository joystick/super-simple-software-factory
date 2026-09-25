# docs/

This directory had no index — five loose top-level files sat at the same level as the
two real subdirectories with nothing pointing at them, found during an opus audit for
duplication/completeness/placement. This file is that index.

## The two standing bodies of material

- **[`reference/`](reference/README.md)** — the complete SSSF concept glossary. Every
  core component (ADW, Gate, Envelope, Phase, Roster, `coding_agent`, the queue's
  Frontier, ...) has a real "what is X" answer here. Start at
  [`reference/concept-manifest.md`](reference/concept-manifest.md) for the full index.
- **[`training/`](training/README.md)** — the learner-facing material: the adoption
  playbook (below) plus an Astro Starlight course, `training/site-starlight/`, taking a
  reader from a first gate they watch fail to a fully unattended dark-factory queue.

## Standing reference docs (top level)

- **[`playbook-adopting-sssf.md`](playbook-adopting-sssf.md)** (+ `.pdf`) — the
  adoption playbook: install, Rule Zero, the four jobs, going dark, the queue. The
  single canonical copy — `docs/training/`'s former copy was a stale duplicate,
  removed (see that directory's `README.md`).
- **[`manual-skill-engineering.md`](manual-skill-engineering.md)** (+ `.pdf`) — the
  `skill_engineering` feature end to end: vendoring, composition order, the coding-agent
  allowlist, token-cost tracking. Cross-linked from
  [`reference/agent-configuration/`](reference/agent-configuration/) and
  [`reference/coding-agent-drivers/`](reference/coding-agent-drivers/).
- **[`head-to-head-agy-vs-claude.md`](head-to-head-agy-vs-claude.md)** — a controlled
  same-task, same-gates comparison of `agy` vs. `claude_code` as the coding-agent
  driver. Cross-linked from
  [`reference/coding-agent-drivers/`](reference/coding-agent-drivers/).

**Known staleness risk:** the `.pdf` renders of the two files above are generated
separately from their `.md` source and are not regenerated automatically on every edit
— treat a `.pdf` as a point-in-time snapshot, the `.md` as the live document, and
re-render before distributing a PDF that matters.

## Historical / decision-record docs (not standing reference — read as "why", not "what is")

- **[`prd-skill-engineering.md`](prd-skill-engineering.md)** — the original PRD that
  proposed `skill_engineering` before it was built. Superseded as a how-to-use-it
  reference by `manual-skill-engineering.md`; kept for the design reasoning.
- **[`research-local-video-generation.md`](research-local-video-generation.md)** —
  feasibility research for generating `training/`'s screencast narration/visuals
  locally (verdict: no, on the hardware tested). Related to `training/`, not to SSSF
  itself — kept here rather than moved, since it's SSSF-repo-specific research, not
  content that belongs inside `training/`'s own script-and-cast layout.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-09-25 | Initial index. Written after an opus audit of `docs/` found the five top-level loose files had no index and were largely unreachable except by directory listing. |
