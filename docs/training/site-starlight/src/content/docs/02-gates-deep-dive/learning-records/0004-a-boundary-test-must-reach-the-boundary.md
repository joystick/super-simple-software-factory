---
title: "A Boundary Test Must Reach the Boundary"
sidebar:
  order: 4
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0004 — A boundary test must use inputs that reach the boundary

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:**
  [0004 — The clamp, and the test that never ran](/02-gates-deep-dive/lessons/0004-the-clamp-and-the-test-that-never-ran/)
- **Objectives:** 2 (domain modelling) and 4 (TDD practice)

## The finding, reproduced in TypeScript

The Python original's clamp test used two 100% discounts. The first alone reaches the
ceiling, so the loop's `if (running >= ceiling) break` fires on the second iteration and
the `Math.min` line never executes. The clamp could be deleted and the test stayed green
for the life of the codebase.

Reproduced here, deliberately, before publishing the lesson. With `Math.min(...)` replaced
by `discount.amountCents`:

| Test                                                      | Result              |
| --------------------------------------------------------- | ------------------- |
| 100% + 100% — "discounts never exceed the subtotal"       | **1 passed**        |
| 60% + 60% — "a partially overflowing discount is clipped" | **1 failed**        |
| whole suite                                               | 48 passed, 2 failed |

The assertion was never wrong. The **inputs** were: 100% + 100% cannot produce a partial
overflow, so it never reaches the line it claims to protect.

## The rule

**Ask of every guard: what input makes this line the one that decides the answer?** If the
test does not contain that input, it is documentation, not a test — it will pass whether
the line exists or not.

## Why this keeps happening

This is the third instance in four lessons, and they share one root — _a claim that was
never executed_:

1. **Lesson 1** — I asserted a type error would trip one gate. `deno test` type-checks, so
   it trips two. Caught by running the table.
2. **Lesson 2** — the float-vs-exact example carried over from Python did not reproduce,
   because `500 * 8.7 / 100` is exactly 43.5 in JavaScript. Caught by probing; replaced
   with 8.7% of 1500c.
3. **Lesson 4** — this one.

Two of the three were mistakes I was about to publish. The habit that caught all three is
the same one the lessons teach, which is the reason to trust it.

## Consequences for this codebase

- Keep the weak 100%+100% test. It documents the invariant readably. It simply is not the
  test that protects it, and the file now says so in a comment.
- The clamp lives in its own small function so the interesting behaviour is isolated and
  re-readable.
- Coverage would have reported the clamp line as covered. Coverage reports which lines
  ran, never whether the assertions around them meant anything.

## Related

- [Reference: testing boundaries](/02-gates-deep-dive/reference/0004-testing-boundaries/)
- [0002 — basis points instead of Decimal](0002-basis-points-instead-of-decimal.md)
- [0001 — deno test type-checks](0001-deno-test-type-checks.md)
