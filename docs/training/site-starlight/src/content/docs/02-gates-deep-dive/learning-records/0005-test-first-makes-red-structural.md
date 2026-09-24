---
title: "Test First Makes Red Structural"
sidebar:
  order: 5
---

:::note[Reference, not practice]
This is a record of real teaching dialogue — the context a lesson was written from, not an exercise. There is nothing here to answer or run; read it for the reasoning, then return to the lessons for the practice.
:::

## 0005 — Test-first makes "watch it fail" structural, not a discipline

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:**
  [0005 — Writing the spec yourself](/02-gates-deep-dive/lessons/0005-writing-the-spec-yourself/)
- **Objective:** 4 — TDD in TypeScript

## The argument this course actually earned

The usual case for TDD is about design and confidence. Those are arguable. This course
produced a narrower, unarguable one from its own mistakes:

| Lesson | The miss                                          | Root                     |
| ------ | ------------------------------------------------- | ------------------------ |
| 1      | Claimed a type error trips one gate; it trips two | claim never executed     |
| 2      | Float example from Python did not reproduce in JS | claim never executed     |
| 4      | Clamp test passed with the clamp deleted          | assertion never executed |

**A test written after the code has never been observed to fail.** You have only seen it
pass; you have no evidence it can do anything else. Every trap above is that gap.

Writing the test first removes the gap by construction. Red stops being a step you have to
remember and becomes the state you are already standing in.

## Teaching-shape change

Lessons 1–4 handed over a failing spec and asked for an implementation. Lesson 5 inverts
it: a behaviour list, an inert test file, and three design decisions left deliberately
unsettled (case sensitivity, whitespace trimming, duplicate coupons). Satisfying a spec is
the easy half; writing one is the skill.

Verified before publishing that the exercise is completable: a reference `CouponDiscount`
takes the suite to 50 green with lint and check clean, and behaves correctly across
matching, non-matching, absent and case-differing codes. Reverted afterwards.

## Two flavours of red in a typed runtime

Worth naming explicitly, because the first one reads as breakage:

1. **Does not compile** — the import does not exist, `deno test` runs _nothing_, and the
   50 passing tests disappear from the output. Legitimate red; says nothing about
   behaviour.
2. **Compiles and fails** — a throwing stub restores the runner, so one test fails for the
   reason intended.

The stub step exists to move from the first to the second. Skipping to an implementation
skips the only moment where the test's ability to fail is observable.

## Related

- [Reference: TDD in Deno](/02-gates-deep-dive/reference/0005-tdd-in-deno/)
- [0004 — a boundary test must reach the boundary](0004-a-boundary-test-must-reach-the-boundary.md)
