---
title: "A Guard Invisible Through the Pipeline"
sidebar:
  order: 6
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0006 — A guard can be invisible through the public entry point

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:**
  [0005 — Writing the spec yourself](/02-gates-deep-dive/lessons/0005-writing-the-spec-yourself/)
- **Objective:** 4 — TDD in TypeScript

## What happened

The coupon spec was finished at 63 green and put through a mutation sweep. Six of seven
mutations were caught. One survived:

| Mutation                            | Result                   |
| ----------------------------------- | ------------------------ |
| comparison inverted (`!==` → `===`) | 10 failed                |
| **empty-cart guard removed**        | **63 passed — SURVIVED** |
| made case-insensitive               | 1 failed                 |
| made whitespace-trimming            | 1 failed                 |
| amount hard-coded to 200            | 12 failed                |
| blank-code validation removed       | 1 failed                 |

There _was_ a test named "an empty cart yields no coupon discount". It did not catch it.

## Why

The test drove through `priceCart`. In that path the guard cannot matter:

- an empty cart has `subtotalCents === 0`
- so `percentOf(0, points)` is `0`
- and `priceCart` already drops discounts with `amountCents <= 0`

So the pipeline erases the difference between "returned null" and "returned a zero-value
discount". The guard was genuinely unreachable _through the public entry point_.

## The fix, and why not deletion

Two defensible responses:

1. **Delete the guard** as dead code, since `priceCart` handles it.
2. **Test at the level where it is observable** — call `apply()` directly.

Chose (2). `PricingRule` is a published contract, not an internal detail: anything can
call `apply()`, and at that level `null` ("not applicable") and `{amountCents: 0}`
("applied, worth nothing") are genuinely different answers. `MemberDiscount`'s equivalent
guard was already covered this way in `rules.test.ts` — the coupon test was the
inconsistent one.

Verified after the fix: removing the guard now gives 63 passed, 1 failed.

## The transferable rule

**Testing only through the public entry point can hide a guard that the entry point's own
behaviour makes redundant.** When a mutation survives, ask at what level the difference is
observable — and test there, or delete the code.

This is the fourth instance of the same family in five lessons. The others were about
inputs that never reached a line; this one is about a _level_ that could not see it.

## Related

- [0004 — a boundary test must reach the boundary](0004-a-boundary-test-must-reach-the-boundary.md)
- [Reference: testing boundaries](/02-gates-deep-dive/reference/0004-testing-boundaries/)
