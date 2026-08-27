---
title: "Handoff — where this work stands and how to pick it up"
version: 1.0
updated: 2026-08-27
status: active
---

# Handoff

The durable copy of the session state. A parallel copy lives in Claude Code's memory
directory (`~/.claude/projects/<path-slug>/`) which is auto-loaded into a fresh session —
but that directory is outside git, machine-local, and its name encodes this repo's
**absolute path**, so it is lost on a rename or a move. **This file is the one that
survives.** If the two disagree, trust this one and refresh the other.

## The three places

| Where | What it is |
|---|---|
| `~/Projects/training/sssf-play` | Python playground. Holds the **skill source** at `.claude/skills/sssf/`, a stamped factory in `adws/`, the cart-pricing target app, docs, and the `learn/` course. |
| `~/Projects/training/pricing-ts` | Deno/TypeScript rebuild of the same pricing engine, with its **own** stamped factory and its own five-lesson course. |
| [`joystick/super-simple-software-factory`](https://github.com/joystick/super-simple-software-factory) | Fork of `disler/super-simple-software-factory`. **Skill-only** — no `adws/`, no app. |

`sssf-play` was a bare `git init`; it shares no history with upstream. Porting to the fork
is a deliberate file copy, never a rebase.

**Direction of travel.** Skill changes are made in `sssf-play/.claude/skills/sssf/` and
copied to the fork. Stamped-factory changes (`adws/adw_modules/*.py`) live per-repo and are
copied between repos by hand — they drift unless synced. `quality.py` is the one module
*designed* to differ per repo: its gate commands are repo-specific and the template keeps
`echo` placeholders deliberately.

## State

```
sssf-play   main 5f107b6   51 tests · lint · typecheck   tag: experiment/opus-planner
pricing-ts  main bb18859   77 tests · lint · typecheck   tag: experiment/agy-vs-claude-claude-side
fork        main 16285ce
```

All clean, all committed, single branch each.

## What exists now that did not before

- **Three coding agents.** `pi`, `claude_code`, `agy` — all in the skill template, mixable
  per agent. `agent_cc.py` and `agent_agy.py` were both written from scratch.
- **Gates wired and verified** in both repos, each watched failing through the ADW.
- **Two `/teach` courses**: `learn/` here (operating SSSF; objective 1 done, objective 2
  next) and `pricing-ts/` (TypeScript; all four objectives done).
- **A head-to-head** between `agy` and `claude` — `docs/head-to-head-agy-vs-claude.md`.
- **A PRD and plan** for `skill_engineering`, unbuilt — `docs/prd-skill-engineering.md`.

## Open

**Nothing is blocked.** Three things were deliberately left:

1. **The dead-gate demo** (~£1). Break `pricing-ts`'s test gate to an `echo`, plant a known
   bug, run a real `just sdlc` on an unrelated feature, watch the factory commit the bug and
   record `5/5 ✓ success`. The mechanism is traced and each link verified in isolation; what
   is missing is watching the whole chain do it. Buys conviction, not information. **Do it
   in a copy of the repo** — a commit containing a deliberate bug should not enter real
   history.
2. **`learn/` objective 2** — reading a trace, and what `sssf.db` structurally cannot tell
   you.
3. **`skill_engineering`** — specified and planned, not built. SSSF agents run with
   `--setting-sources ''` and therefore cannot see installed skills; verified by probe.

## Things that will bite if forgotten

- **`just sdlc` gates on tests only** (`run_tests`, 1 of 3). Lint and typecheck are wired
  and verified but do not run in that chain. Run `just quality` afterwards — it is free.
- **`commit_all` stages the entire working tree.** Clean tree, throwaway branch, every time.
- **A green banner means the gates you verified found nothing.** Nothing more. This is the
  whole subject of `learn/`.

## The one idea underneath all of it

A gate has two states that are **identical from outside**: it checked and found nothing
wrong, or it is incapable of finding anything. Green does not distinguish them; neither does
reading the command. Only a deliberate defect does.

Four separate bugs this session were the same failure — a claim nobody executed. The clamp
test that passed with the clamp deleted. The percentages that were all binary-representable.
The guard invisible through the public entry point. The gate table that was simply wrong.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-08-27 | Initial handoff. |
