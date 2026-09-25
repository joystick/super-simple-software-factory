---
title: Chains
---

# Chains

A chain is an ADW script that runs several phases in sequence, threading each
agent's envelope into the next call. SSSF ships two chains that matter when
reading the rest of this glossary: `adw_plan_build_test.py` (the "full
starter chain") and `adw_simple_sdlc.py` (the full SDLC, with review and
documentation). The queue watcher's module docstring is where the two are
named side by side and the choice between them is justified:

> dispatch it through the full SDLC chain (planner -> builder -> reviewer ->
> revision loop -> documenter -> commit -- adw_simple_sdlc.py, not the
> lighter plan_build_test chain -- an unattended queue dispatch gets no other
> independent check besides the test gate, so it needs the review/revision
> loop a supervised manual run could otherwise skip).

Source: `.claude/skills/sssf/templates/adws/adw_watch.py:5-10`.

## Why two chains exist

Both chains share the same core — planner, builder, a bounded test/fix loop
where testing is *code*, and a commit only after the suite is green. They
differ in what independent checks sit between "the builder says it's done"
and "it's on the branch":

| | `adw_plan_build_test.py` | `adw_simple_sdlc.py` |
|---|---|---|
| Required roster | `planner`, `builder` (`:28`) | `planner`, `builder`, `reviewer`, `documenter` (`:52`) |
| Phases | request → plan → build → test [→ fix → test]×3 → commit (`:10`) | request → plan → commit_plan → build → test [→ fix]×3 → review [→ revise]×2 → retest → commit_build → changes → document → commit_docs (`:10-14`) |
| Independent checks | the test suite only | the test suite **and** a reviewer against the plan |
| Commits | one, after green tests (`:81-86`) | three — plan, code, docs — "three work products, three authors" (`:16-20`) |
| Build gate | `artifacts_exist` (`:61`) | `diff_matches_claims` (`:94`) |
| `--skip-plan` | yes (`:97-98`) | no |

The lighter chain is the one an engineer runs by hand: they read the plan,
watch the build, and are themselves the second check. The heavier chain
exists for the case where nobody is watching. Its own docstring makes the
point that the suite and the reviewer answer *different* questions — "The
suite asks 'does it run'; the reviewer asks 'is this what was asked for',
against `plan.md` — and neither can answer the other's" (`adw_simple_sdlc.py:27-31`)
— and that a revision which closes a review finding re-enters the suite, so
"the tree that gets committed is the tree that was both tested and approved."

## Which chain runs where

- `just watch` (the queue) always dispatches `adw_simple_sdlc.py` — never a
  per-ticket choice, for the reason quoted above. See
  [The queue watcher (just watch)](../the-queue/The-queue-watcher.md) and [Dark factory](../the-queue/Dark-factory.md)'s "The
  chain named once".
- `adw_plan_build_test.py` (and its siblings `adw_plan_build.py`,
  `adw_build_test.py`, `adw_plan_build_test_quality.py` under
  `templates/adws/`) are the supervised, manually invoked forms.

## How a chain threads state

Every agent phase is a `ph.call(AgentCall(...))` whose `previous=` is the
envelope from the step before ([AgentCall](AgentCall.md)). Code
phases feed back in through the same door via adapters —
`quality.as_envelope(test, "tests")` for a red suite
(`adw_simple_sdlc.py:111`), `changes.as_envelope(changeset, ...)` for the
documenter (`:166`). Nothing is passed between agents outside an envelope.

## See also

- [The queue watcher (just watch)](../the-queue/The-queue-watcher.md) — the caller that runs the heavier chain
  unattended.
- [Dark factory](../the-queue/Dark-factory.md) — why the queue names exactly one chain.
- [--skip-plan](Skip-plan.md) — the flag only the lighter chains
  accept.
