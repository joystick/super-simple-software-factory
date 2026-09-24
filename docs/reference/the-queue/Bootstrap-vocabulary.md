---
title: Bootstrap vocabulary
---

# Bootstrap vocabulary

"Bootstrap vocabulary" is the human-supervised step that runs **before** a
headless loop starts: when a feature introduces domain concepts the project
has not named yet, the operator runs `/grill-with-docs` interactively, it
writes the resolved terms to `CONTEXT.md`/`docs/adr/`, and those files are
**committed** before `just sdlc` (or `just watch`) touches the request.
Source: `docs/playbook-adopting-sssf.md`, Part C, "Problem 1" (lines
473–536). It is one half of the **bootstrap / AFK split** — the other half
being the common, headless case where the request only composes terms
`CONTEXT.md` already names and no human step is needed.

## Why it exists

`wayfinder`'s "ask the user how to proceed" fallback assumes an interactive
session. Vendored under `skill_engineering:` on a headless `claude_code`
node, "there is no one there" — best case the model role-plays both sides
and produces a low-fidelity spec, worst case the run hangs on input that
never comes (playbook, lines 475–480). The playbook's fix is explicit: **do
not delete the interview — relocate it**, because the interview is how a
project converges on shared vocabulary (is "account" the Customer or the
User?), and that cannot be skipped just because a run is unattended.

Three consequences define the concept:

- **Commit, or it didn't happen.** Scout and the planner read `CONTEXT.md`/
  `docs/adr/` from the working tree, not from any live session; skipping the
  commit "makes the whole bootstrap step invisible to the pipeline"
  (lines 492–495). This is a "Definition of done" item (lines 591–592).
- **The AFK side is overrides in `system.md`, not edits to vendored skills.**
  `to-spec` runs unmodified ("no interview, just synthesis"); the agent's own
  `system.md` tells it that no-fog means continue into `to-spec`, that a
  genuine ambiguity is flagged as provisional in `notes_for_next_agent` rather
  than guessed silently or prompted for, and that `to-tickets`'s quiz never
  applies in-loop (lines 496–515).
- **`grill-with-docs` stays out of `skill_engineering/`.** Its
  `disable-model-invocation: true` is load-bearing: vendoring it risks it
  firing headless, "exactly the failure this split exists to prevent"
  (lines 533–536). It is one of the two interactive-only skills
  `the-queue/Dark-factory.md` lists alongside `triage`.

The grill → `/triage` handoff is deliberately manual (lines 569–585): nothing
bridges a settled `CONTEXT.md` into the queue, so a bootstrapped feature that
never reaches `/triage` is invisible to `just watch`. The checklist line
"run `/triage` before leaving the session" (lines 599–603) is the guard.

## See also

- `the-queue/Dark-factory.md` — the goal state this step makes possible, and
  the five vendored vs. two interactive-only skills.
- `the-queue/The-queue-watcher.md` — what consumes the ticket once it is
  `ready-for-agent`.
- `the-queue/The-four-jobs.md` — the architecture job, where the interview
  normally sits in a supervised adoption.
- `docs/playbook-adopting-sssf.md` — Part C in full, including Problem 2
  (scout's glossary → knowledge source → structural search order).
- `../../training/site-starlight/src/content/docs/06-going-dark/lessons/0001-bootstrap-vocabulary.mdx`
  — the full lesson this entry summarises.
