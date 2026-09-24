---
title: Four-param rule
---

# Four-param rule

The four-param rule is the one API-shape rule the ADW harness imposes on
itself: any function that would take **more than four parameters takes one
typed object instead**. It is stated, in exactly those terms, at the top of
the data-types module — the module docstring names both the rule and its two
canonical instances:

```python
"""Concrete data types for the SSSF ADW system.

RULE (four-param rule): any function that takes more than 4 parameters takes
ONE of these objects instead. AgentCall and PhaseParams are the pattern.
...
"""
```

Source: `.claude/skills/sssf/templates/adws/adw_modules/data_types.py:1-8`.

## Why it exists

An ADW script is a straight-line sequence of `run.phase(...)` / `ph.call(...)`
statements — it is meant to read like the chain it describes, not like a
function-call puzzle. Loose positional parameters break that in two ways the
rule closes off:

- **Readability at the call site.** `run.phase(PhaseParams(name="build",
  kind="agent", owner="builder", description="Implement the plan exactly"))`
  says what every value *is*; the same four values passed positionally do not.
  `PhaseParams`'s own docstring puts it in one line: "Everything run.phase()
  needs. Passed as one object, never loose params." (`data_types.py:22-23`).
- **Validation at construction time.** Because the parameters are a Pydantic
  model, the harness can enforce rules on them before anything runs. The
  clearest example is `PhaseParams.description`, whose validator rejects a
  blank description *and* one that merely restates the phase name — "a
  construction-time error on purpose: it fires before the phase opens, not
  after a run is already in the trace" (`data_types.py:31-53`). A bare
  `description: str` parameter could not do that.

The rule is applied uniformly, not just where the docstring names it.
`ChangeCapture` carries the same sentence — "Everything
documentation.capture() needs. One object, never loose params."
(`data_types.py:177-182`) — and `changes.capture(run, params: ChangeCapture)`
takes it as its single argument (`adw_modules/changes.py:52`).

## The pattern objects

| Object | Consumed by | Lines in `data_types.py` |
|---|---|---|
| `PhaseParams` | `run.phase(...)` — opens a phase block | 22-53 |
| `AgentCall` | `ph.call(...)` — one agent invocation | 286-294 |
| `ChangeCapture` | `changes.capture(run, ...)` — deterministic diff capture | 177-182 |

Each is a plain `BaseModel` with typed, commented fields. When you add a
phase or a code block that needs a fifth argument, the rule says: do not add
the argument — add a field to the object, or make a new one.

## See also

- `core-execution-model/AgentCall.md` — the second of the two named pattern
  objects, and what `ph.call()` does with it.
- `handoff-and-output/ChangeSet-and-BaseRef.md` — `ChangeCapture` in use, the
  third object built on the same rule.
- `.claude/skills/sssf/references/handoff.md#the-typed-output-rule` — the
  companion rule for the *output* side: every agent call declares a concrete
  envelope type, "no untyped handoffs" (`data_types.py:6-7`).
