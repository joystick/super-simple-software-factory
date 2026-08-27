# 0001 — A green gate result carries almost no information

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:** [0001 — A gate you have not watched fail](../lessons/0001-a-gate-you-have-not-watched-fail.html)
- **Objective:** 1 — gates

## The misconception this replaced

Asked what `3/3 passed` establishes about an unfamiliar repo, the answer given was:

> "the repo has a test suite which passes, it has a linter and maybe some other
> typechecker tools wired and they also return 0"

Demonstrated false immediately: a repo containing one `app.py` and no tooling whatsoever
reports `checks: 4/4, status ✓ success`, because a freshly stamped factory ships every
quality block as `echo 'PLACEHOLDER …'`, and `echo` exits 0.

## The idea everything else follows from

A gate has two states that are **identical from outside**:

1. it checked something and found nothing wrong
2. it is incapable of finding anything wrong

A green result does not distinguish them. Neither does the trace.

Reading the command helps but is not sufficient — verified: `deno test --filter "smoke"`
exits 0 having run zero of 66 tests. Real runner, real command, no placeholder, nothing
checked.

## The procedure

Per gate, separately: introduce a defect of the class **that tool** exists to catch, run
every gate, require the target red **and all others green**, restore.

The "all others green" half is what isolates. Without it, red-on-target cannot be
distinguished from everything-is-red.

## Two things that were not obvious and had to be shown

**Why per gate.** A dead lint gate plus a real bug: the build goes red (test caught it),
so a team that stops at "the build went red" concludes all three gates work. Fix the bug
and the dead gate is indistinguishable from a healthy one.

**Why the probe must match the tool.** "Extra spaces" was proposed as a lint probe.
Measured: `pytest=PASS ruff=PASS mypy=PASS`. Whitespace is a formatter's concern. Used as
a probe it produces a *false diagnosis* — the gate looks dead when it is healthy. An
unused import gives clean isolation: `pytest=PASS ruff=FAIL mypy=PASS`.

## The consequence that makes this matter

A dead gate does not merely fail to catch bugs. SSSF's fix loop is fed by gate failures,
so when the gate is an `echo` the loop **never fires** — the builder is never told
anything is wrong — the commit phase sees green and commits, and the trace records
`status ✓ success · phases 5/5`. It disables the repair machinery and then certifies the
result. Worse than no factory, because the trace now resembles evidence.

## Learner patterns worth carrying forward

- **Label-matching under pressure**, twice: applying a just-taught hazard (pipes masking
  exit codes) to an unrelated question, and picking the wrong row of the diagnosis table
  for a both-red result. Counter-move: ask "what is this tool's *job*" before asking what
  to conclude.
- **Overclaim drift**: "the gate works" became "the code works". A verified gate
  establishes that the behaviours it covers are genuinely checked — never that the code is
  correct. Verification buys a working instrument, not coverage.

## Also learned, by my own error

While building a demonstration I measured an exit code through a pipe and reported the
wrong result — `deno lint lib/ | tail -3` yields `tail`'s exit code, not deno's. Caught
and corrected in front of the learner. This is exactly why `quality.py` insists `argv` be
a **list, never a shell string**: a list means no shell, so no pipe can eat the verdict.

## Related

- [Reference: verifying a gate](../reference/0001-verifying-a-gate.html)
- `docs/playbook-adopting-sssf.md` — rule zero
