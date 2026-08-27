# 0002 — There are two families of gate, and lesson 1 taught one

- **Date:** 2026-08-25
- **Status:** accepted
- **Lesson:** [0002 — Wiring and writing gates](../lessons/0002-wiring-and-writing-gates.html)
- **Objective:** 1 — gates

## What prompted this

The learner asked whether they were missing a practical guide on "writing (or wiring?)
gates" — noticing the ambiguity themselves. Checking the codebase before answering turned
up a larger gap than the question implied.

## The distinction they spotted

| Act | Means | Where |
|---|---|---|
| **Wiring** | pointing a block at a command that already exists | `quality.py` |
| **Writing** a check | authoring the command itself, usually a test | the test suite |
| **Writing** a gate | authoring a function that judges an agent's claims | `gates.py` |

## The gap that was bigger

Lesson 1 covered **quality blocks** only — commands that judge the code. SSSF has a second
family: **envelope gates**, `gate(envelope, run) -> GateReport`, which judge the agent's
*claims about its own work*.

Demonstrated with `artifacts_exist` against fabricated envelopes:

```
claims app/pricing.py  (real)       OK    app/pricing.py    exists, 7.9KB
claims specs/ghost.md  (invented)   FAIL  specs/ghost.md    declared artifact does not exist
```

This is the more SSSF-specific family. An envelope is a set of claims, and nothing about
producing that JSON requires any of it to be true. Envelope gates are "agent proposes,
code disposes" applied to the *report* rather than the code.

Shipped: `artifacts_exist`, `files_non_empty`, `json_parses`, `diff_matches_claims`,
`verdict_consistent`, and the `tests_pass(command)` factory.

## The design detail worth keeping

A gate records **every** check, passing ones included, so a green gate says *what it
verified* rather than merely that it passed:

```
OK    justfile          exists, 4.4KB
FAIL  specs/ghost.md    declared artifact does not exist
```

A gate returning a bare boolean would reproduce lesson 1's problem one level up — green
would carry no information about what was examined.

And `note` on a failed check becomes the violation text, which is sent back into the
**same agent session** as a correction, bounded by the phase's `retries`. Notes are
written for the agent that must act on them, not for a log.

## Symmetry between the families

- quality block fails → output feeds the **fix loop** → builder repairs → gate re-runs
- envelope gate fails → violations become a **correction** in the same session

Both treat a failure as an input to the next attempt rather than an error to report.

## Another self-inflicted correction

The first run of the demo labelled `README.md` as an artifact that "exists". The gate said
it did not. **The gate was right** — this repo has no README.md — and the label was mine.
Third time this session that checking a claim beat asserting it, and the second time the
tool was right and I was wrong.

## Related

- [Reference: gate cookbook](../reference/0002-gate-cookbook.html)
- [0001 — green does not mean wired](0001-green-does-not-mean-wired.md)

## Postscript — the exercise, and a bad steer

The learner attempted `no_placeholder_blocks` and got the scaffolding right: signature,
`GateReport()`, the `run.repo_root` path, `ast.parse`, and the loop filtering to
`FunctionDef`. One line was broken — `ast.RetunType`, which is not a typo for anything
real — and it came from my hint to look at `node.returns`.

They then said plainly that they are not a Python developer. That reframes the exercise:
the Python was never the point, and asking them to reason about annotation nodes taught
nothing about gates.

**The better signal, and the one worth remembering:** the blocks are exactly the names
`run_quality()` runs. Ask the file rather than inferring from type annotations. It is
simpler, and it means a block deliberately deleted from that list — as `build` was here —
is correctly ignored by the gate too.

Verified both directions:

```
this repo (wired)        OK/OK/OK                    violations: 0
fresh stamp (untouched)  FAIL x4 (test/lint/typecheck/build)  violations: 4
```

The limitation is written into the docstring rather than left implied: it catches blocks
nobody has edited, and cannot catch a block edited into something hollow — `["echo","ok"]`
or a filter matching no tests. Only watching a gate fail settles that.
