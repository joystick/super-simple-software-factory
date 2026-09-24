---
title: "Context Object Over Parameter List"
sidebar:
  order: 3
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0003 — A rule takes a context object, not a parameter list

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:** [0003 — The shape of a rule](/02-gates-deep-dive/lessons/0003-the-shape-of-a-rule/)
- **Objective:** 2 — TypeScript domain modelling

## Decision

`PricingRule.apply` takes a single `PricingContext` object. Widening the contract means
adding a field to that interface; no existing rule changes.

## The evidence this is the right call

The Python original took the parameter-list route, and the coupon rule proved it wrong in
two stages:

1. The first implementation absorbed the new argument with `**_kwargs` on every rule. That
   compiles and silently swallows misspellings forever — `cupon_code=` produces a rule
   that never fires and a discount that simply is not on the receipt.
2. The second named `coupon_code` explicitly on every rule, which restored the error but
   still required editing every rule to accept a field most of them ignore.

A context object removes the dilemma rather than choosing a side of it.

## `implements` — verified, not assumed

TypeScript is structural, so the clause is optional. What it changes is where a mismatch
is reported. Both messages below were produced by `deno check` against a class with a
misspelled method:

| Written as               | Error                           | Reported at               |
| ------------------------ | ------------------------------- | ------------------------- |
| no clause                | `TS2741` property missing       | the **use** site (line 5) |
| `implements PricingRule` | `TS2420` incorrectly implements | the **class** (line 2)    |

Both catch it. Only one points at the line that is wrong. Use `implements`.

## Absence is a decision

A rule that does not apply returns `null`, never a zero-valued `Discount`. They are
different claims: "not relevant" versus "applied, worth nothing" — and the second is a
line a customer can see and query.

## Carried forward

- Types are erased. `readonly` is a compile-time promise; `Object.freeze` is the runtime
  half. This has now come up in lessons 1 and 3 and will keep coming up.
- Freeze a **copy** of an array you were handed, or the caller keeps a mutable handle to
  your internals.

## Related

- [Reference: types and contracts](/02-gates-deep-dive/reference/0003-types-and-contracts/)
- [0002 — basis points instead of Decimal](0002-basis-points-instead-of-decimal.md)
