---
title: "Deno Test Type Checks"
sidebar:
  order: 1
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0001 — `deno test` type-checks, so the gates are not independent

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:**
  [0001 — Three gates you have watched fail](/02-gates-deep-dive/lessons/0001-three-gates-you-have-watched-fail/)
- **Objective:** 1 — run SSSF against TypeScript repositories

## What happened

Lesson 1 was drafted with a table claiming three defects would each trip exactly one gate.
The table was run before publishing. Two rows held; one did not.

Introducing a type error turned **both** `deno test` and `deno check` red:

```
test=PASS lint=FAIL check=PASS   unused variable
test=FAIL lint=PASS check=FAIL   wrong param type   <- claimed "check only"
test=FAIL lint=PASS check=PASS   wrong arithmetic
```

## Why

`deno test` type-checks the module graph before executing it. There is no separate compile
step in Deno, so type errors surface through the test runner as well.

This differs from the Python original, where `pytest` and `mypy` share nothing and the
three gates really are orthogonal.

## What this means going forward

- In Deno, `test` is a **superset** of `check`. `check` is the fast subset.
- `deno check` is still worth gating on: it is much faster, and it covers files that no
  test imports — which is where type rot collects as a codebase grows.
- When isolating a genuine behavioural failure from a type failure, use
  `deno test --no-check`.
- When SSSF's `quality.py` is wired to this project (objective 1), the `typecheck` block
  is **not** redundant with `test`, but a red `typecheck` will usually be accompanied by a
  red `test`. Read `typecheck` first — its message is the clearer one.

## The meta-lesson

The claim was plausible, matched the Python mental model, and was wrong. It was caught
only because the table was executed rather than reasoned about. This is the same failure
mode the course warns about from the other direction: **an unverified claim about a gate
is exactly as untrustworthy as an unverified gate.**

## Related

- [Reference: Deno gate commands](/02-gates-deep-dive/reference/0001-deno-gates/)
