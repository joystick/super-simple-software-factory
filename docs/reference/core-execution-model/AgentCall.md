---
title: AgentCall
---

# AgentCall

`AgentCall` is the single object an ADW hands to `ph.call(...)` to run one
agent: the prompt going in, the envelope type the agent's final JSON is
parsed against, the previous envelope to inject, and the gates that verify
the result. Its docstring is the whole contract in one line: "One agent
invocation: prompt in, typed envelope out, gates verified."

```python
class AgentCall(BaseModel):
    """One agent invocation: prompt in, typed envelope out, gates verified."""

    model_config = {"arbitrary_types_allowed": True}

    output_type: Type[EnvelopeBase]
    prompt: str
    previous: Optional[EnvelopeBase] = None
    gates: list[Callable] = Field(default_factory=list)   # gate(envelope, run) -> list[str]
```

Source: `.claude/skills/sssf/templates/adws/adw_modules/data_types.py:286-294`.

## Why it exists

`AgentCall` is one of the two named instances of the four-param rule
(`data_types.py:3-4`, see `core-execution-model/Four-param-rule.md`): rather
than `ph.call(output_type, prompt, previous, gates, ...)`, an ADW passes one
object whose fields are named at the call site. It also enforces the typed
output rule mechanically — `output_type` is not optional, so there is no way
to invoke an agent without declaring what shape its answer must take
(`data_types.py:6-7`: "Every agent call declares a concrete output type — an
EnvelopeBase subclass — that its final JSON response is parsed against. No
untyped handoffs.").

## The four fields

| Field | What it does |
|---|---|
| `output_type` | The `EnvelopeBase` subclass (`PlanOutput`, `BuildOutput`, `ReviewOutput`, ...) the agent's final JSON is parsed into. Required. |
| `prompt` | The engineer's request — usually the same string threaded through every phase of a chain. |
| `previous` | The envelope from the phase before, or `None` for the first agent. Rendered into the `previous_envelope` prompt variable. |
| `gates` | Functions run against the parsed envelope after the session ends. Empty list = nothing verified beyond the parse itself. |

Note the field comment on `gates` says `gate(envelope, run) -> list[str]`,
but the gates the harness actually ships return a `GateReport`
(`adw_modules/gates.py`, and `quality-gates-and-permissions/Gate.md`). The
comment is a stale shorthand for "a list of violations" — `GateReport.violations`
is that list (`data_types.py:277-279`). Author new gates to the `GateReport`
shape.

## What consumes it

`ph.call(call)` (`adw_modules/runner.py:36-39`) refuses to run outside an
`agent`-kind phase and then delegates to `agents.execute(run, phase, call)`
(`adw_modules/agents.py:228-229`), whose docstring is the pipeline: "render
prompts -> pi run -> typed parse -> gates -> envelope." Two of the call's
fields become prompt variables directly (`agents.py:235-237`):

```python
variables = {
    "prompt": call.prompt,
    "previous_envelope": call.previous.model_dump_json(indent=2) if call.previous else "(none)",
    ...
```

`previous` being an envelope — not a path, not a string — is what makes a
chain a chain: the builder receives the planner's `PlanOutput` verbatim, the
documenter receives a `ChangesOutput` that *code* produced
(`handoff-and-output/ChangeSet-and-BaseRef.md`), and both arrive through the
same door.

## In an ADW

```python
with run.phase(PhaseParams(name="build", kind="agent", owner="builder",
                           description="Implement the plan exactly")) as ph:
    build = ph.call(AgentCall(output_type=BuildOutput, prompt=prompt, previous=plan,
                              gates=[gates.diff_matches_claims]))
```
(`templates/adws/adw_simple_sdlc.py:91-94`)

## See also

- `core-execution-model/Four-param-rule.md` — the rule `AgentCall` is the
  named example of.
- `quality-gates-and-permissions/Gate.md` — what goes in `gates`, and the
  `GateReport` shape they actually return.
- `.claude/skills/sssf/references/handoff.md#injecting-the-previous-envelope` —
  how `previous` reaches the agent's prompt.
