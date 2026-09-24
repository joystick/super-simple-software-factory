---
title: "Basis Points Instead of Decimal"
sidebar:
  order: 2
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0002 — Basis points are the TypeScript answer to Python's `Decimal`

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:**
  [0002 — Money without a decimal type](/02-gates-deep-dive/lessons/0002-money-without-a-decimal-type/)
- **Objective:** 2 — TypeScript domain modelling

## Decision

Percentages are stored as **integer basis points** (1 bp = 0.01%), not as floats and not
via a decimal library. `percentOf` is `Math.round((amountCents * points) / 10_000)`.

## Why not the alternatives

- **Float percentages** put an inexact value in the middle of otherwise-exact integer
  arithmetic. Measured: over 16,000 combinations (8 fractional percentages × amounts
  1–2000c), the float route disagreed with exact arithmetic **105 times**, always by one
  cent, always against the customer.
- **A decimal library** means a dependency in the pricing hot path and an API every caller
  must remember. The precision it buys is finer than any shop quotes.
- **TC39 decimal** has not shipped.

## The cost accepted

Precision floor of 0.01%. Anything finer rounds half-up to the nearest basis point. This
is stated in the spec rather than left implicit, because an unstated precision limit is
how you end up with 267.49999 basis points and no idea why.

## What nearly went wrong when writing this

The lesson was going to use "8.7% of 500c" as the headline example, carried over from the
Python original where that case was the one that exposed the bug.

**In JavaScript it does not reproduce.** `500 * 8.7 / 100` evaluates to exactly `43.5`,
because that particular rounding error cancels. Probing before publishing found this and
the example was replaced with a verified one: **8.7% of 1500c**, where the float route
gives 130 and the correct half-up answer is 131.

The general lesson is bigger than the example: **a numeric bug that looks intermittent is
usually systematic and badly sampled.** Two different languages, the same percentage, and
a different set of amounts expose it — because what matters is which products happen to
land on a representable value.

## Testing consequence

Numeric tests must deliberately use values that are _not_ binary-representable: 8.7,
2.675, 0.7, 3.3. Round numbers and halves (12.5, 7.25, 5) agree under both routes and will
pass a suite that is completely blind to the defect. This is the exact failure that hid
the bug in the Python original for its whole life.

## Related

- [Reference: money and rounding](/02-gates-deep-dive/reference/0002-money-and-rounding/)
- [0001 — deno test type-checks](0001-deno-test-type-checks.md)
