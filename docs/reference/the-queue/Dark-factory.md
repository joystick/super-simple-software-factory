---
title: Dark factory
---

# Dark factory

"Dark factory" is the operating mode where the queue runs unattended — no
human in the loop between a ticket becoming `ready-for-agent` and the work
landing, reviewed and committed. The term names the *goal state* of Part D of
the adoption playbook (`docs/playbook-adopting-sssf.md`): a factory that can
keep working with the lights off.

## The chain named once

Every dispatch the watcher runs goes through the **same** chain:
`adw_simple_sdlc.py`'s full planner → builder → reviewer → revision loop →
documenter → commit sequence — never the lighter `plan_build_test`. The
watcher module's own docstring states why explicitly: an unattended dispatch
gets no other independent check besides the test gate, so it needs the
review/revision loop a supervised, interactively-run chain could otherwise
skip. See [The queue watcher (just watch)](The-queue-watcher.md) for the full mechanics. Naming the
chain once, here, matters pedagogically: a reader should never wonder "which
chain does the queue use" — it's always this one, on purpose, not a per-ticket
choice.

## The two layers

The playbook frames SSSF as two layers that meet only at points an operator
chooses: the harness layer (ADWs, gates, permissions — everything covered in
categories 1–5 of this glossary) and the vendored-skill layer
(`skill_engineering` — wayfinder, to-spec, to-tickets, tdd, code-review). The
queue is where both layers run together headlessly: the watcher (harness
layer) dispatches into a chain whose planner role has these skills vendored
in (skill layer). See `.claude/skills/sssf/references/config.md#skill-engineering`
for the vendoring mechanism itself.

## The five vendored skills

The standard roster vendors five skills onto specific roles (see the
playbook's "Cheat sheet" section for the full table):

| Skill | Role | Mode |
|---|---|---|
| `wayfinder` | planner | headless, no-fog fallthrough forced |
| `to-spec` | planner | headless, never interviews |
| `to-tickets` | planner | headless, quiz skipped |
| `tdd` | planner | headless, pure methodology |
| `code-review` | reviewer | headless, spec always supplied |

Two more skills exist but are deliberately **not** vendored — they only run
interactively, by a human, outside any agent: `grill-with-docs` (bootstrap
vocabulary interviews, Stage 0) and `triage` (the judgment gate that flips a
ticket to `ready-for-agent` in the first place — see below).

## Triage states and the agent brief

Tickets move through five canonical states (`needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`), owned by the interactive
`triage` skill. `just watch` never makes this judgment call itself — it
trusts that a ticket reaching `ready-for-agent` already passed a human's
feasibility/compatibility/compliance/security check, and only ever consumes
that state, never re-derives it (`adw_watch.py:22-28`, module docstring). The
ticket body itself, verbatim, becomes the "agent brief" — the literal prompt
handed to the dispatched chain (`utils.resolve_prompt(str(issue.path))`,
`adw_watch.py:286`).

## Issue tracker and ticket files

The queue currently supports one tracker: local markdown, detected via
`docs/agents/issue-tracker.md`'s first line (`detect_tracker`,
`adw_watch.py:321-332`) — GitHub/GitLab are explicitly detected and refused
with a clear error, not silently mishandled. Tickets are files at
`.scratch/<feature>/issues/NN-slug.md`, parsed into an `Issue` dataclass
(path, number, feature, status, blocked_by) by `discover_issues()`
(status constants at `adw_watch.py:100-103`, the function itself at
`adw_watch.py:184-207`).

## Mandatory checkpoints

Even in dark-factory mode, the system is designed around checkpoints a human
still owns: triage (promoting a ticket to `ready-for-agent`) is the sole
promoter into the queue, and a failed dispatch always flips back to
`ready-for-human` rather than looping or sitting silently `claimed` forever —
see [The queue watcher (just watch)](The-queue-watcher.md)'s crash-handling section. "Dark" means
unattended between checkpoints, not unsupervised entirely.

## See also

- [The queue watcher (just watch)](The-queue-watcher.md) — the scan-claim-dispatch-resolve
  mechanics `just watch` runs.
- [Frontier](Frontier.md) — how the next ticket is chosen.
- `.claude/skills/sssf/references/config.md#skill-engineering` — how a skill
  gets vendored onto a role.
