---
title: "Resources"
description: "External sources for Chapter 2 — Gates, deep dive."
---

High-trust sources for this mission. Prefer these over anything I assert from memory.

## Primary — Deno

| Resource                                                                        | Use it for                                                           | Trust        |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------ |
| [Deno — Testing](https://docs.deno.com/runtime/fundamentals/testing/)           | `Deno.test`, steps, hooks, filtering, coverage, per-test permissions | Official     |
| [@std/assert (JSR)](https://jsr.io/@std/assert)                                 | the assertion API the specs import                                   | Official std |
| [deno lint](https://docs.deno.com/runtime/reference/cli/lint/)                  | rules, tags, inline ignores                                          | Official     |
| [deno fmt](https://docs.deno.com/runtime/reference/cli/fmt/)                    | formatting options in `deno.json`                                    | Official     |
| [Deno configuration](https://docs.deno.com/runtime/fundamentals/configuration/) | `deno.json`: tasks, imports, fmt, lint                               | Official     |

## Primary — TypeScript

| Resource                                                                                   | Use it for                               | Trust    |
| ------------------------------------------------------------------------------------------ | ---------------------------------------- | -------- |
| [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)             | the language itself                      | Official |
| [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)                 | discriminated unions — objective 2       | Official |
| [Type Compatibility](https://www.typescriptlang.org/docs/handbook/type-compatibility.html) | structural typing vs Python's `Protocol` | Official |

## Numbers and money

| Resource                                                          | Use it for                       | Trust                   |
| ----------------------------------------------------------------- | -------------------------------- | ----------------------- |
| [IEEE 754 / floating point guide](https://floating-point-gui.de/) | why `0.1 + 0.2 !== 0.3`          | Community, widely cited |
| [TC39 Decimal proposal](https://github.com/tc39/proposal-decimal) | why JS still has no decimal type | Official proposal       |

## Communities — for wisdom, not knowledge

Real feedback beats any lesson I write. Worth joining one:

- [Deno Discord](https://discord.gg/deno) — active, maintainers present
- [r/typescript](https://www.reddit.com/r/typescript/) — design-level discussion
- [TypeScript Community Discord](https://discord.gg/typescript)

Post the pricing module once objective 3 lands and ask what they would change. The answers
you get from practitioners are the part I cannot supply.

## Reference in this workspace

- The Python original: `~/Projects/training/sssf-play/app/pricing.py` and its 51 tests.
  **Consult it after attempting a slice, never before.**

## Version history

| Version | Date       | Changes                                          |
| ------- | ---------- | ------------------------------------------------ |
| 1.0     | 2026-08-25 | Initial list, gathered while preparing lesson 1. |
