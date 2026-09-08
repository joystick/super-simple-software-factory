---
title: "Handoff — where this work stands and how to pick it up"
version: 1.2
updated: 2026-09-08
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
fork        main   up to date with origin (skill_engineering merged, --skip-plan ported)
```

All clean, all committed, single branch each.

## Fork skill fixes (2026-08-30, committed 2026-09-08) — made while dogfooding the skill in a real project

Both surfaced while running `just obs` from a downstream Expo project (`~/Projects/training/opencode-expo`)
that installs this skill. Sat uncommitted for over a week; reviewed and committed 2026-09-08:

- **`.claude/skills/sssf/scripts/install.py`** — `install` did not vendor the visualizer app, so
  `just obs` in a target repo had no server to run. Added `SKILL_ROOT` + a `SKIP_NAMES` set
  (`__pycache__`, `node_modules`, `dist`, `.turbo`) and now copy `apps/visualizer` into the target
  plus the matching `.gitignore` entries.
- **`.claude/skills/sssf/apps/visualizer/server/db.ts`** — opened `sssf.db` `{ readonly: true }`,
  which throws `CANTOPEN` on a **WAL** database (WAL needs to touch `-wal`/`-shm`). Changed to
  `{ readwrite: true, create: false }` — opens the existing WAL db without creating a new one.

`just obs` (Vue/bun visualizer at `.claude/skills/sssf/apps/visualizer`) works after these.

## What exists now that did not before

- **Three coding agents.** `pi`, `claude_code`, `agy` — all in the skill template, mixable
  per agent. `agent_cc.py` and `agent_agy.py` were both written from scratch.
- **Gates wired and verified** in both repos, each watched failing through the ADW.
- **Two `/teach` courses**: `learn/` here (operating SSSF; objective 1 done, objective 2
  next) and `pricing-ts/` (TypeScript; all four objectives done).
- **A head-to-head** between `agy` and `claude` — `docs/head-to-head-agy-vs-claude.md`.
- **`skill_engineering` — built.** Landed upstream in the fork (6 phases + 4 rounds of
  adversarial review, `skill_engineering.py`/`vendor_skill.py`/`adw_skills.py`), pulled into
  this repo 2026-09-08. Reviewed post-pull — findings filed, none blocking (missing test
  coverage on an unrelated small `load_plan_from_file` addition, and an unvalidated `--as`
  path-traversal case in `vendor_skill.py`, both low severity).

## Open

**Nothing is blocked.** Two things were deliberately left:

1. **The dead-gate demo** (~£1). Break `pricing-ts`'s test gate to an `echo`, plant a known
   bug, run a real `just sdlc` on an unrelated feature, watch the factory commit the bug and
   record `5/5 ✓ success`. The mechanism is traced and each link verified in isolation; what
   is missing is watching the whole chain do it. Buys conviction, not information. **Do it
   in a copy of the repo** — a commit containing a deliberate bug should not enter real
   history.
2. **`learn/` objective 2** — reading a trace, and what `sssf.db` structurally cannot tell
   you.

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
| 1.1 | 2026-08-30 | Recorded two uncommitted fork skill fixes (`install.py` visualizer-vendoring, `db.ts` WAL read-write) found while dogfooding `just obs` downstream. |
| 1.2 | 2026-09-08 | Committed and pushed the two fork skill fixes. Pulled 21 upstream commits, including `skill_engineering` (now built) and the adoption-playbook rework; reviewed, findings filed. |
