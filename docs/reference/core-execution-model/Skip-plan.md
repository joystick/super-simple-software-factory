---
title: --skip-plan
---

# `--skip-plan`

`--skip-plan PLAN_FILE` is a CLI flag on the supervised chains that replaces
the planner phase with a *code* phase: instead of invoking the planner agent,
the ADW loads an already-written plan file into a `PlanOutput` envelope via
`utils.load_plan_from_file()` and carries on to the builder. The function's
docstring states the intent:

```python
def load_plan_from_file(path: str) -> PlanOutput:
    """Build a PlanOutput from an already-written plan file, for --skip-plan.

    Used when a plan has already been read and approved (the ADW's own
    planner phase always writes to specs/<adw_id>_*.md) and re-running the
    planner would just burn tokens re-deriving the same document. The file
    becomes the plan's sole artifact, so downstream gates (artifacts_exist,
    files_non_empty) still check something real rather than being skipped.
    """
```

Source: `.claude/skills/sssf/templates/adws/adw_modules/utils.py:66-89`.

## Why it exists

The planner always writes its spec to `specs/<adw_id>_*.md`. The normal
workflow is to run `adw_plan.py` (or a full chain), read that spec, and
approve it — at which point re-running the planner to get the same document
back is pure cost. `adw_plan_build_test.py`'s docstring says exactly this:
"useful once you've read a plan from a prior run of this or `adw_plan.py` and
just want it built, without paying to re-derive the same document"
(`adw_plan_build_test.py:16-19`).

The design detail worth noticing is that skipping the planner does **not**
skip the plan's gates. `load_plan_from_file` puts the file path in
`artifacts=[str(p)]`, so the downstream `artifacts_exist` /
`files_non_empty` checks still run against something real. It also fails
loudly rather than proceeding on a bad input — a missing file raises
`FileNotFoundError`, an empty one `ValueError` (`utils.py:77-82`).

## What the envelope looks like

| `PlanOutput` field | Value |
|---|---|
| `status` | `"success"` |
| `summary` | `"Loaded existing plan: <first non-blank line, `#` stripped>"` |
| `artifacts` | `[<the plan file path>]` |
| `notes_for_next_agent` | `"Plan was loaded from an existing file (--skip-plan), not freshly generated."` |

(`utils.py:83-89`.) The `notes_for_next_agent` line is deliberate: the builder
is told, inside its `previous_envelope`, that this plan was not produced in
its own run.

## In the chain

```python
if skip_plan:
    with run.phase(PhaseParams(name="plan", kind="code", owner="engineer",
                               description="Load an already-approved plan instead of re-planning")) as ph:
        plan = utils.load_plan_from_file(skip_plan)
        ph.log(loaded_from=skip_plan)
else:
    with run.phase(PhaseParams(name="plan", kind="agent", owner="planner", ...)) as ph:
        plan = ph.call(AgentCall(output_type=PlanOutput, prompt=prompt,
                                 gates=[gates.artifacts_exist, gates.files_non_empty]))
```
(`adw_plan_build_test.py:47-56`)

The phase keeps the name `plan` but changes `kind` from `agent` to `code` and
`owner` to `engineer` — so a trace shows plainly that a human, not the
planner, supplied this plan.

## Where it is accepted

`--skip-plan` exists on `adw_plan_build_test.py` (`:97-98`) and
`adw_plan_build.py` (`:8, 37-40`). It is **not** on `adw_simple_sdlc.py`, and
therefore never reaches the queue — an unattended dispatch always plans
fresh (`core-execution-model/Chains.md`).

## See also

- [Chains](Chains.md) — which chains take the flag and which do
  not.
- [Gate](../quality-gates-and-permissions/Gate.md) — `artifacts_exist` and
  `files_non_empty`, the gates a loaded plan still has to pass.
- `.claude/skills/sssf/references/handoff.md#envelope-schema` — the
  `PlanOutput` / `EnvelopeBase` fields the loader fills in.
