---
title: The four jobs
---

# The four jobs

"The four jobs" is the adoption playbook's classification of what an operator
can hand a factory in an existing codebase — **improve architecture**, **find
and fix bugs**, **implement a feature**, **refactor into reusable
abstractions** — each with a different entry ritual and a different cheap
checkpoint before `just sdlc` runs. Source: `docs/playbook-adopting-sssf.md`,
section "A5. The four jobs" (Part A, lines 158–234), including its Mermaid
decision diagram. (The concept manifest points at Part D; the section
actually lives in Part A.)

## Why it exists

Every job ends at the same place — `just sdlc`, then "review the diff, not
the banner" — but the *cheapest place to catch a misunderstanding* differs
per job, so the playbook refuses to treat them as one prompt shape:

| Job | Before `just sdlc` | Cheap checkpoint |
|---|---|---|
| Improve architecture | `/grill-with-docs` → `/to-spec` → `/to-tickets` (A4), then `just plan` on **one slice** | read `specs/<adw_id>_*.md` yourself; re-plan if the design was misunderstood — one planner run instead of a full build plus a bad diff |
| Find and fix bugs | reproduce as a **failing test**, commit it red | the prompt must say "do not modify the test" — the builder has write access and deleting an assertion is the cheapest path to green |
| Implement a feature | state it narrowly, name the tests A, B, C | keep the slice small enough that one plan can express it; cost scales with plan size (`just sessions`) |
| Refactor | check coverage; if thin, spend a run on **characterisation tests first** and commit them | an explicit no-behaviour-change constraint; the unchanged green suite is the evidence the refactor was safe |

Two of these get a highlighted node in the diagram — reading the spec, and
characterisation tests first — because they are the checkpoints operators
most often skip. The refactor job is called out as "the most dangerous"
because "working" and "unchanged" are different claims; without pinned tests
"you are not refactoring, you are rewriting and hoping" (playbook, lines
221–234).

## Where it sits

A5 comes after recon (A1), wired gates (A2, rule zero), boundaries (A3), and
interrogation (A4). It assumes the gates are real: the bug and refactor jobs
in particular are only meaningful when the test block in
`adws/adw_modules/quality.py` actually runs your suite.

## See also

- `quality-gates-and-permissions/Rule-zero.md` — the gates every job relies on.
- `quality-gates-and-permissions/Quality-blocks.md` — the test/lint blocks
  that grade each job's output.
- `the-queue/Bootstrap-vocabulary.md` — the interview step the architecture
  job starts from, and how it moves out of the loop when going dark.
- `docs/playbook-adopting-sssf.md` — "A5. The four jobs".
- `../../training/site-starlight/src/content/docs/03-adopting-a-factory/lessons/0002-the-four-jobs.mdx`
  — the full lesson.
