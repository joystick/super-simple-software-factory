---
title: Gate
---

# Gate

A Gate is a function that checks what an agent's envelope **claims** against
what is actually on disk — never a guess, never a re-read of the whole diff
for quality. `gates.py`'s own docstring states the boundary precisely: "Gates
check what is mechanically checkable; plan quality is a reviewer's job."

## Why it exists

An agent's envelope is a claim — "I wrote these three files," "the review
approved with no blocking items." Nothing forces that claim to be true. A
Gate is the harness verifying the claim mechanically, in code, after the
agent session ends — the same "verify after the fact" philosophy that
`quality-gates-and-permissions/Permissions-and-writes.md` uses for write
access. A gate that fails sends the violation back to the **same agent
session** as a correction, not a fresh restart — the agent gets to fix its
own claim.

## Shape

```python
def gate(envelope: EnvelopeBase, run) -> GateReport: ...
```

Source: `.claude/skills/sssf/templates/adws/adw_modules/gates.py:1-9`.

Every gate returns a `GateReport` (a list of `GateCheck`s — see
`quality-gates-and-permissions/Permissions-and-writes.md` for the sibling
enforcement concepts, and `.claude/skills/sssf/templates/adws/adw_modules/data_types.py:252-279`
for the two Pydantic models themselves). Authoring one is "a loop and a
return":

```python
def files_non_empty(envelope: EnvelopeBase, run) -> GateReport:
    report = GateReport()
    for a in envelope.artifacts:
        ...
        report.check(a, not empty, "declared artifact is empty" if empty else _size(p))
    return report
```
(`gates.py:36-44`)

The key design choice: `report.check(item, ok, note)` records **every**
check, not just failures. A green gate says *what* it verified, not only
that nothing broke — so a passing gate is itself evidence, readable later in
the trace (see `observability/`).

## Built-in gates

All in `.claude/skills/sssf/templates/adws/adw_modules/gates.py`:

| Gate | What it verifies | Lines |
|---|---|---|
| `artifacts_exist` | every path the envelope declares as an artifact exists on disk | 27-33 |
| `files_non_empty` | those artifacts aren't zero-byte | 36-44 |
| `json_parses` | any `.json` artifact actually parses | 47-58 |
| `diff_matches_claims` | every file the envelope claims as changed exists | 61-68 |
| `verdict_consistent` | a review's `approved`/`blocking`/`findings` don't contradict each other | 71-95 |
| `tests_pass(command)` | a gate **factory** — wraps any shell command, gate passes iff exit 0 | 98-108 |

`verdict_consistent` is worth reading closely — it checks the envelope
against *itself* (an approval that ships blocking items, or a rejection that
names no problem), not against the code. That is deliberate: judging code
quality is the reviewer agent's job; the gate only refuses to let an
internally-contradictory verdict pass silently.

## Gates vs. permission enforcement

A Gate failure is recoverable — the harness re-prompts the same session with
the violation and gives it another try. A permission breach
(`quality-gates-and-permissions/Permissions-and-writes.md`) is not: the write
already happened, so the phase aborts instead of looping. Keep the two
separate when reading a failed run's trace — "gate failed" means a claim
didn't check out; "permission breach" means the agent touched something it
wasn't allowed to.

## See also

- `quality-gates-and-permissions/Permissions-and-writes.md` — the companion
  enforcement mechanism for *what an agent may write*, as opposed to *what it
  claims it did*.
- `quality-gates-and-permissions/Rule-zero.md` — why gates must be wired and
  proven to fail before any agent runs against them.
- `.claude/skills/sssf/references/handoff.md#the-typed-output-rule` — the
  envelope shape gates are checking claims against.
