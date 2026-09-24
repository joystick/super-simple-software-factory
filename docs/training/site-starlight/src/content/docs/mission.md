---
title: "Mission"
description: "Objectives for the SSSF course, chapter by chapter."
---

Operate SSSF for real — not demo it. Gates are the cornerstone: everything else the
factory offers rests on the guarantee that an agent's *claims* are replaced by a
*deterministic verdict* before work proceeds. A factory is exactly as trustworthy as its
weakest gate, and a gate's trustworthiness cannot be read, only demonstrated.

This course has two chapters. Chapter 1 builds the general operating picture in the
Python playground (`sssf-play`). Chapter 2 takes gates deep — same cornerstone, harder
material, a second language (TypeScript/Deno) as the vehicle so the lesson is proven
independent of any one toolchain.

## Chapter 1 — SSSF fundamentals (`chapters/01-sssf-fundamentals/`)

Source repo: `~/Projects/training/sssf-play`.

### 1. Gates — ✅ DONE (lessons 0001, 0002)

Know what a gate is, why a green result carries almost no information, and how to verify
one by mutation. Assessed by dialogue rather than assertion; see learning record 0001.

Then both families: **quality blocks** judge the code, **envelope gates** judge the
agent's claims about its own work. Wiring one, writing the other. See learning record
0002. Outstanding: the hands-on task in lesson 2 — write `no_placeholder_blocks`, a gate
that fails a run whose quality blocks are still placeholders.

### 2. Bound an agent — ✅ DONE (lesson 0006)

`writes`, `protected_files`, and the reason the builder must not be able to edit its own
grader. What each mechanism does and does not prevent.

### 3. Carry a workflow protocol into a headless run — ✅ DONE (lesson 0007)

Interactive skills (`/tdd`, `/codebase-design`) are invisible to a headless agent by
default. `skill_engineering` closes that gap for a skill you vendor and name on purpose,
per agent — a prompt change only; the outcome gates still do all the checking.

### 4. Read a trace and know what it does not say — ✅ DONE (lesson 0008)

The trace records what ran and what it cost. It cannot record whether the checks meant
anything. Learn to read `sssf.db` for the questions it can answer, and to notice the ones
it cannot.

### 5. Compose your own chain — ✅ DONE (lesson 0009)

An ADW is a thin Python script naming a phase sequence and its gates. Copy the closest
one, edit the phase list, own your own workflow.

### 6. Run the factory on work that matters — ✅ DONE (lesson 0010)

A real feature on a real repo, reviewed properly — diff read, cost checked, gates trusted
because they were verified.

## Chapter 2 — Gates, deep dive (`chapters/02-gates-deep-dive/`)

Source repo: `~/Projects/training/pricing-ts`. Rebuilds the playground's cart pricing
engine — 220 lines of Python behind 51 tests — from scratch in TypeScript on Deno, and
uses the rebuild as the vehicle for four objectives, taken in order. The point is not
TypeScript for its own sake: it is proof that the gate discipline from Chapter 1 survives
a change of language, toolchain and domain-modelling idiom.

### 1. Run SSSF against TypeScript repositories — ✅ DONE

A real Deno project with real, verified gates that an SSSF `quality.py` can be wired to.
`deno test`, `deno lint` and `deno check` each watched failing through the factory, not
just in a terminal, before being trusted.

### 2. Learn TypeScript domain modelling deeply — ✅ DONE (lessons 2–4)

How the Python original's ideas land in a structural type system: the `PricingRule`
Protocol's nearest TS equivalent, exhaustive validation that raises rather than returns,
money as integer cents with no `Decimal` type to lean on.

### 3. Port the pricing logic for real use — ✅ DONE

A module good enough to ship, not a teaching toy: published interface (`mod.ts`),
documented invariants, every documented example executed by `deno test --doc` and wired
into the gate.

### 4. Practise TDD in TypeScript — ✅ DONE (lesson 5)

Red-green-refactor with a known-good target — the Python suite is the spec, so the
answer is always available for comparison after the fact.

### Known traps carried over from the Python build

Both found the hard way in the original repo, both the same underlying lesson:

- A test asserting a clamp that never exercised it — two 100% discounts hit the ceiling
  before the clamp was consulted, so deleting the clamp kept the suite green.
- Every percentage in the suite being exactly representable in binary floating point, so a
  float-vs-exact bug was invisible until `8.7%` was tried.

**When a deliberate break does not fail the suite, suspect the test.** This is the same
claim Chapter 1 makes about gates in general — Chapter 2 is where it gets tested against
a harder case.

## Constraint

Nothing is taken on the operator's word. Every claim in these lessons was executed on
this machine before it was written, and where a claim turned out wrong it is corrected in
place with the correction visible.

## Version history

| Version | Date | Changes |
|---|---|---|
| 2.1 | 2026-09-07 | Marked Chapter 1 objectives 2–4 done (lessons 0006, 0008, 0010 now exist) and renumbered them 2–6 to add a new objective 3: carrying a workflow protocol into a headless run via `skill_engineering` (lesson 0007). |
| 2.0 | 2026-08-27 | Merged the `sssf-play` and `pricing-ts` courses into this single course under `~/Projects/training/sssf-learn/`, as Chapter 1 (fundamentals) and Chapter 2 (gates deep dive). Superseded `sssf-play/learn/MISSION.md` (was v1.0) and `pricing-ts/MISSION.md` (was v1.2). |
